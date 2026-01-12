import subprocess
import logging
import tempfile
import time
import os
from pathlib import Path
from typing import Optional, List, Dict, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import MigrationConfig, AuthConfig

class GitMigrator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def migrate_batch(
        self,
        migrations: List[MigrationConfig],
        max_concurrent: int = 3,
        retry_on_failure: bool = True,
        max_retries: int = 2,
        retry_delay: int = 5,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Executa migração em lote com controle de concorrência
        
        Args:
            migrations: Lista de migrações a executar
            max_concurrent: Número máximo de migrações simultâneas
            retry_on_failure: Se True, tenta novamente em caso de falha
            max_retries: Número máximo de tentativas
            retry_delay: Delay em segundos entre tentativas
            progress_callback: Função callback para progress tracking
        
        Returns:
            Dicionário com resultados das migrações
        """
        self.logger.info(f"Iniciando migração em lote com {len(migrations)} repositórios")
        self.logger.info(f"Concorrência máxima: {max_concurrent}")
        
        results = {
            'total': len(migrations),
            'success': 0,
            'failed': 0,
            'details': [],
            'failed_migrations': []
        }
        
        retry_queue = []
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submete todas as migrações
            future_to_migration = {
                executor.submit(self.migrate, migration): migration
                for migration in migrations
            }
            
            completed = 0
            # Processa resultados conforme completam
            for future in as_completed(future_to_migration):
                migration = future_to_migration[future]
                completed += 1
                
                try:
                    success = future.result()
                    
                    if success:
                        results['success'] += 1
                        self.logger.info(f"✓ [{completed}/{len(migrations)}] {migration.name}")
                    else:
                        results['failed'] += 1
                        results['failed_migrations'].append(migration.name)
                        
                        if retry_on_failure and max_retries > 0:
                            retry_queue.append((migration, 1))
                        
                        self.logger.error(f"✗ [{completed}/{len(migrations)}] {migration.name}")
                    
                    results['details'].append({
                        'name': migration.name,
                        'success': success,
                        'retry': False
                    })
                    
                    if progress_callback:
                        progress_callback(completed, len(migrations))
                        
                except Exception as e:
                    results['failed'] += 1
                    self.logger.error(f"Exceção durante migração de {migration.name}: {str(e)}")
                    results['failed_migrations'].append(migration.name)
        
        # Processa fila de retry
        if retry_queue and max_retries > 0:
            results = self._process_retries(
                retry_queue,
                max_concurrent,
                max_retries,
                retry_delay,
                results
            )
        
        return results
    
    def _process_retries(
        self,
        retry_queue: List,
        max_concurrent: int,
        max_retries: int,
        retry_delay: int,
        results: Dict
    ) -> Dict:
        """Processa fila de retry com backoff"""
        self.logger.info(f"Processando {len(retry_queue)} migrações com falha para retry")
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            future_to_migration = {}
            
            for migration, attempt in retry_queue:
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    self.logger.info(f"Tentativa {attempt + 1}/{max_retries} para {migration.name}")
                    
                    future = executor.submit(self.migrate, migration)
                    future_to_migration[future] = (migration, attempt + 1)
            
            for future in as_completed(future_to_migration):
                migration, attempt = future_to_migration[future]
                
                try:
                    success = future.result()
                    
                    if success:
                        results['success'] += 1
                        results['failed'] -= 1
                        results['failed_migrations'].remove(migration.name)
                        self.logger.info(f"✓ [RETRY {attempt}] {migration.name}")
                    else:
                        self.logger.error(f"✗ [RETRY {attempt}] {migration.name}")
                    
                    # Atualiza detalhe com retry
                    for detail in results['details']:
                        if detail['name'] == migration.name:
                            detail['retry'] = True
                            detail['retry_attempt'] = attempt
                            break
                            
                except Exception as e:
                    self.logger.error(f"Erro em retry de {migration.name}: {str(e)}")
        
        return results
    
    def migrate(self, migration: MigrationConfig) -> bool:
        """Executa migração de um repositório para outro"""
        self.logger.debug(f"Iniciando migração: {migration.name}")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Clone com autenticação
                self._mirror_clone(
                    migration.source.url,
                    temp_path,
                    migration.source.auth
                )
                
                # Push com autenticação
                self._push_to_destination(
                    temp_path,
                    migration.destination.url,
                    migration.destination.auth,
                    migration.options
                )
                
                return True
                
        except Exception as e:
            self.logger.error(f"Erro na migração '{migration.name}': {str(e)}")
            return False
    
    def _mirror_clone(
        self,
        source_url: str,
        dest_path: Path,
        auth: Optional[AuthConfig] = None
    ) -> None:
        """Faz clone em mirror com suporte a autenticação"""
        self.logger.debug(f"Clonando em mirror de {source_url}")
        
        # Prepara URL com credenciais
        url = self._prepare_url(source_url, auth)
        
        cmd = [
            'git',
            'clone',
            '--mirror',
            url,
            str(dest_path / 'repo.git')
        ]
        
        self._run_command(cmd, "Clone em mirror", auth)
    
    def _push_to_destination(
        self,
        repo_path: Path,
        dest_url: str,
        auth: Optional[AuthConfig] = None,
        options: Optional[dict] = None
    ) -> None:
        """Faz push para repositório de destino com autenticação"""
        mirror_path = repo_path / 'repo.git'
        self.logger.debug(f"Fazendo push para {dest_url}")
        
        # Prepara URL com credenciais
        url = self._prepare_url(dest_url, auth)
        
        cmd = [
            'git',
            '-C', str(mirror_path),
            'push',
            '--mirror',
            url
        ]
        
        self._run_command(cmd, "Push em mirror", auth)
    
    def _prepare_url(self, url: str, auth: Optional[AuthConfig]) -> str:
        """Prepara URL com credenciais baseado no tipo de autenticação"""
        if not auth:
            return url
        
        if auth.type == 'token':
            # Para HTTPS com token: https://token@github.com/user/repo.git
            if url.startswith('https://'):
                url = url.replace('https://', f'https://{auth.token}@')
            return url
        
        elif auth.type == 'basic':
            # Para HTTPS com basic auth: https://user:pass@github.com/user/repo.git
            if url.startswith('https://'):
                url = url.replace('https://', f'https://{auth.username}:{auth.password}@')
            return url
        
        elif auth.type == 'ssh':
            # SSH não precisa de modificação na URL
            return url
        
        return url
    
    def _run_command(
        self,
        cmd: list,
        description: str,
        auth: Optional[AuthConfig] = None
    ) -> str:
        """Executa comando Git com suporte a autenticação SSH"""
        try:
            env = os.environ.copy()
            
            # Configura variáveis de ambiente para SSH se necessário
            if auth and auth.type == 'ssh' and auth.ssh_key:
                env['GIT_SSH_COMMAND'] = f'ssh -i {auth.ssh_key} -o StrictHostKeyChecking=no'
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                env=env
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"{description} falhou: {result.stderr}")
            
            self.logger.debug(f"{description} executado com sucesso")
            return result.stdout
            
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"{description} excedeu tempo limite")
        except Exception as e:
            raise RuntimeError(f"Erro ao executar {description}: {str(e)}")
    
    def validate_credentials(self, url: str, auth: Optional[AuthConfig] = None) -> bool:
        """Valida acesso ao repositório com autenticação"""
        self.logger.debug(f"Validando credenciais para {url}")
        
        try:
            prepared_url = self._prepare_url(url, auth)
            cmd = ['git', 'ls-remote', prepared_url]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.warning(f"Erro ao validar credenciais: {str(e)}")
            return False
