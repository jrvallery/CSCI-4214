from unittest.mock import MagicMock, patch
import data_agent.pipeline.embedder as embedder_module


def test_vertexai_init_called_once_across_multiple_embed_calls():
    mock_embedding = MagicMock()
    mock_embedding.values = [0.1, 0.2, 0.3]
    mock_model = MagicMock()
    mock_model.get_embeddings.return_value = [mock_embedding]

    with patch("data_agent.pipeline.embedder.vertexai.init") as mock_init, \
         patch("data_agent.pipeline.embedder.TextEmbeddingModel.from_pretrained", return_value=mock_model) as mock_from_pretrained, \
         patch.dict("os.environ", {"GCP_PROJECT": "test-project"}):
        embedder_module._model = None  # reset cached model before test
        try:
            embedder_module.embed_batch(["text one"])
            embedder_module.embed_batch(["text two"])
        finally:
            embedder_module._model = None  # restore to clean state

    assert mock_init.call_count == 1, f"vertexai.init called {mock_init.call_count} times, expected 1"
    assert mock_from_pretrained.call_count == 1, f"from_pretrained called {mock_from_pretrained.call_count} times, expected 1"
