# Splatfacto

Owns the only supported Gaussian Splat training path.

Target responsibilities:

- Convert selected frames and COLMAP output into Nerfstudio data.
- Run `ns-train splatfacto` with CUDA-only assumptions.
- Stream loss and quality metrics into the job metrics API.
- Export browser-viewable splat assets.
