import api


def test_default_model_adapter_is_the_live_detector_endpoint():
    """O painel nao pode sondar um adaptador legado inexistente enquanto o detector vive em :8093."""
    assert api.ADAPTADOR == "http://127.0.0.1:8093"
