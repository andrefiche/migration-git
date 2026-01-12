import yaml
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class AuthConfig:
    type: str  # token, ssh, basic
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_key: Optional[str] = None

@dataclass
class SourceConfig:
    url: str
    branch: str = "main"
    auth: Optional[AuthConfig] = None

@dataclass
class DestinationConfig:
    url: str
    create_if_missing: bool = True
    auth: Optional[AuthConfig] = None

@dataclass
class MigrationConfig:
    name: str
    source: SourceConfig
    destination: DestinationConfig
    options: Dict[str, Any]

class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self.migrations: List[MigrationConfig] = []
        
    def load(self) -> List[MigrationConfig]:
        """Carrega configurações do arquivo YAML"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        self._validate_config(config)
        self._parse_migrations(config)
        self.logger.info(f"Carregadas {len(self.migrations)} migrações da configuração")
        return self.migrations
    
    def _validate_config(self, config: Dict) -> None:
        """Valida estrutura da configuração"""
        if not config or 'migrations' not in config:
            raise ValueError("Configuração deve conter seção 'migrations'")
        
        if not isinstance(config['migrations'], list):
            raise ValueError("'migrations' deve ser uma lista")
    
    def _parse_migrations(self, config: Dict) -> None:
        """Parseia migrações da configuração"""
        for migration_data in config['migrations']:
            # Parse source
            source_data = migration_data['source']
            source_auth = self._parse_auth(source_data.get('auth'))
            source = SourceConfig(
                url=source_data['url'],
                branch=source_data.get('branch', 'main'),
                auth=source_auth
            )
            
            # Parse destination
            dest_data = migration_data['destination']
            dest_auth = self._parse_auth(dest_data.get('auth'))
            destination = DestinationConfig(
                url=dest_data['url'],
                create_if_missing=dest_data.get('create_if_missing', True),
                auth=dest_auth
            )
            
            options = migration_data.get('options', {})
            
            migration = MigrationConfig(
                name=migration_data['name'],
                source=source,
                destination=destination,
                options=options
            )
            self.migrations.append(migration)
    
    def _parse_auth(self, auth_data: Optional[Dict]) -> Optional[AuthConfig]:
        """Parseia configuração de autenticação e expande variáveis de ambiente"""
        if not auth_data:
            return None
        
        auth_type = auth_data.get('type', 'ssh')
        
        # Expande variáveis de ambiente
        token = auth_data.get('token')
        if token and token.startswith('${') and token.endswith('}'):
            env_var = token[2:-1]
            token = os.getenv(env_var)
            if not token:
                raise ValueError(f"Variável de ambiente '{env_var}' não definida")
        
        ssh_key = auth_data.get('ssh_key')
        if ssh_key:
            ssh_key = os.path.expanduser(ssh_key)
        
        auth = AuthConfig(
            type=auth_type,
            token=token,
            username=auth_data.get('username'),
            password=auth_data.get('password'),
            ssh_key=ssh_key
        )
        
        self._validate_auth(auth)
        return auth
    
    def _validate_auth(self, auth: AuthConfig) -> None:
        """Valida configuração de autenticação"""
        if auth.type == 'token' and not auth.token:
            raise ValueError("Autenticação 'token' requer campo 'token'")
        elif auth.type == 'basic' and (not auth.username or not auth.password):
            raise ValueError("Autenticação 'basic' requer 'username' e 'password'")
        elif auth.type == 'ssh':
            if auth.ssh_key and not Path(auth.ssh_key).exists():
                raise ValueError(f"Chave SSH não encontrada: {auth.ssh_key}")
    
    def setup_logging(self, config: Dict) -> None:
        """Configura logging baseado na configuração"""
        log_config = config.get('logging', {})
        level = log_config.get('level', 'INFO')
        log_file = log_config.get('file', 'migration.log')
        
        logging.basicConfig(
            level=getattr(logging, level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
