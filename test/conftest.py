def pytest_configure(config):
    config.addinivalue_line("markers", "networktest: This test uses the network.")
