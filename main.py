import sys
import logging
import yaml
from pathlib import Path
from config import ConfigManager
from migrator import GitMigrator

def print_progress(current: int, total: int) -> None:
    """Exibe progresso da migração"""
    percentage = (current / total) * 100
    print(f"Progresso: [{current}/{total}] {percentage:.1f}%")

def print_summary(results: dict) -> None:
    """Exibe resumo detalhado dos resultados"""
    print("\n" + "="*50)
    print("=== RESUMO DA MIGRAÇÃO ===")
    print("="*50)
    print(f"Total de repositórios: {results['total']}")
    print(f"✓ Sucesso: {results['success']}")
    print(f"✗ Falhas: {results['failed']}")
    
    if results['failed_migrations']:
        print(f"\nRepositórios com falha:")
        for name in results['failed_migrations']:
            print(f"  - {name}")
    
    print("="*50 + "\n")

def main():
    config_path = "config.yaml"
    
    # Verifica se caminho customizado foi passado
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    try:
        # Carrega configuração
        config_manager = ConfigManager(config_path)
        
        # Setup logging
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        config_manager.setup_logging(config_data)
        
        logger = logging.getLogger(__name__)
        logger.info("=== Iniciando aplicação de migração Git ===")
        
        # Carrega migrações
        migrations = config_manager.load()
        
        if not migrations:
            logger.error("Nenhuma migração configurada")
            return 1
        
        # Obtém configurações de batch
        batch_config = config_data.get('batch', {})
        max_concurrent = batch_config.get('max_concurrent', 3)
        retry_on_failure = batch_config.get('retry_on_failure', True)
        max_retries = batch_config.get('max_retries', 2)
        retry_delay = batch_config.get('retry_delay', 5)
        
        # Executa migrações em lote
        migrator = GitMigrator()
        
        logger.info(f"Validando acesso aos repositórios de destino...")
        for migration in migrations:
            if not migrator.validate_credentials(migration.destination.url):
                logger.warning(f"Aviso: Não foi possível validar acesso a {migration.destination.url}")
        
        logger.info(f"Iniciando migração em lote de {len(migrations)} repositórios...")
        
        results = migrator.migrate_batch(
            migrations,
            max_concurrent=max_concurrent,
            retry_on_failure=retry_on_failure,
            max_retries=max_retries,
            retry_delay=retry_delay,
            progress_callback=print_progress
        )
        
        # Exibe resumo
        print_summary(results)
        logger.info(f"Migração concluída - Sucesso: {results['success']}, Falhas: {results['failed']}")
        
        return 0 if results['failed'] == 0 else 1
        
    except FileNotFoundError as e:
        print(f"Erro: {e}")
        return 1
    except ValueError as e:
        print(f"Erro de configuração: {e}")
        return 1
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
