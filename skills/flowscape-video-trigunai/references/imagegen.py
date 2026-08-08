"""
Model-agnostic text->image helper so the engine runs on SDXL OR Flux with no
code change — just flip config.IMAGE_MODEL (or the IMAGE_MODEL env var).

  SDXL  (stabilityai/stable-diffusion-xl-base-1.0)  ~7GB   commercial (OpenRAIL++)
  Flux-schnell (black-forest-labs/FLUX.1-schnell)   ~34GB  Apache-2.0 commercial
  (do NOT use FLUX.1-dev commercially — non-commercial license)

Returns (pipe, gen) where gen(prompt, seed, negative=...) -> PIL image.
"""
import config as C


def load_pipeline():
    import torch
    model = C.IMAGE_MODEL
    is_flux = "flux" in model.lower()
    if is_flux:
        from diffusers import FluxPipeline
        pipe = FluxPipeline.from_pretrained(model, torch_dtype=torch.bfloat16)
        is_schnell = "schnell" in model.lower()
        defaults = dict(steps=(4 if is_schnell else 28), guidance=(0.0 if is_schnell else 3.5))
    else:
        from diffusers import StableDiffusionXLPipeline
        pipe = StableDiffusionXLPipeline.from_pretrained(
            model, torch_dtype=torch.float16, variant="fp16", use_safetensors=True)
        defaults = dict(steps=30, guidance=7.0)
    pipe.enable_model_cpu_offload()  # fits the 24GB A10G either way

    def gen(prompt, seed=0, negative="", steps=None, guidance=None):
        g = torch.Generator("cpu").manual_seed(seed)
        kw = dict(prompt=prompt, height=C.TARGET_H, width=C.TARGET_W,
                  num_inference_steps=steps or defaults["steps"],
                  guidance_scale=guidance if guidance is not None else defaults["guidance"],
                  generator=g)
        if not is_flux and negative:      # SDXL supports negative prompts; Flux does not
            kw["negative_prompt"] = negative
        return pipe(**kw).images[0]

    return pipe, gen
