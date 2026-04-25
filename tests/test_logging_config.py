import logging

from app import logging_config


def test_setup_logging_idempotente(monkeypatch, tmp_path):
    monkeypatch.setattr(logging_config, 'logs_dir', lambda: tmp_path)

    root1 = logging_config.setup_logging()
    handlers_1 = [h for h in root1.handlers if getattr(h, '_automacao_file_handler', False)]
    assert len(handlers_1) == 1

    root2 = logging_config.setup_logging()
    handlers_2 = [h for h in root2.handlers if getattr(h, '_automacao_file_handler', False)]
    assert len(handlers_2) == 1
    assert handlers_1[0] is handlers_2[0]

    arquivo = tmp_path / 'automacao.log'
    logging.getLogger('teste').warning('linha de teste')
    handlers_2[0].flush()
    assert arquivo.exists()
    assert 'linha de teste' in arquivo.read_text(encoding='utf-8')

    root2.removeHandler(handlers_2[0])
    handlers_2[0].close()
