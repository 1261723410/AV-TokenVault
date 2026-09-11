def test_sentence_transformer_text_embedder_returns_embedding_result():
    from app.encoders.text_embedding import SentenceTransformerTextEmbedder

    class FakeSentenceTransformer:
        def encode(self, text: str, normalize_embeddings: bool = True):
            assert text == "音视频 token 化"
            assert normalize_embeddings is True
            return [0.1, 0.2, 0.3]

    embedder = SentenceTransformerTextEmbedder(
        model_name="BAAI/bge-small-zh-v1.5",
        model_factory=lambda model_name, device=None, cache_folder=None: FakeSentenceTransformer(),
    )

    result = embedder.encode_text("音视频 token 化")

    assert result.encoder_name == "sentence-transformers:BAAI/bge-small-zh-v1.5"
    assert result.modality == "text"
    assert result.vector == [0.1, 0.2, 0.3]


def test_sentence_transformer_text_embedder_accepts_numpy_like_vectors():
    from app.encoders.text_embedding import SentenceTransformerTextEmbedder

    class FakeVector:
        def tolist(self):
            return [0.4, 0.5]

    class FakeSentenceTransformer:
        def encode(self, text: str, normalize_embeddings: bool = True):
            return FakeVector()

    embedder = SentenceTransformerTextEmbedder(
        model_name="BAAI/bge-small-zh-v1.5",
        model_factory=lambda model_name, device=None, cache_folder=None: FakeSentenceTransformer(),
    )

    assert embedder.encode_text("hello").vector == [0.4, 0.5]
