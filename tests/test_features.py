from pathlib import Path

from PIL import Image

from src.features import FeatureExtractor


def test_feature_extractor_shape_and_norm(tmp_path: Path):
    image_path = tmp_path / "img.jpg"
    Image.new("RGB", (200, 120), (120, 80, 40)).save(image_path)

    extractor = FeatureExtractor(bins=16)
    emb = extractor.extract(str(image_path), bbox=(20, 20, 180, 100))

    assert len(emb) == 64
    norm = sum(x * x for x in emb) ** 0.5
    assert abs(norm - 1.0) < 1e-6
