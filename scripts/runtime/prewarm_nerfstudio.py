"""Prewarm runtime imports and cache directories for offline Splatfacto runs."""

from pathlib import Path


def main() -> None:
    cache_root = Path("/opt/3dgs-cache")
    for child in ["torch", "huggingface", "nerfstudio"]:
        (cache_root / child).mkdir(parents=True, exist_ok=True)

    import torch  # noqa: F401
    import nerfstudio  # noqa: F401
    from torchmetrics.image.lpip import LearnedPerceptualImagePatchSimilarity
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator  # noqa: F401

    LearnedPerceptualImagePatchSimilarity(normalize=True)
    lpips_checkpoint = cache_root / "torch" / "hub" / "checkpoints" / "alexnet-owt-7be5be79.pth"
    if not lpips_checkpoint.exists():
        raise RuntimeError(f"LPIPS AlexNet checkpoint was not cached: {lpips_checkpoint}")

    print("nerfstudio prewarm ok")


if __name__ == "__main__":
    main()
