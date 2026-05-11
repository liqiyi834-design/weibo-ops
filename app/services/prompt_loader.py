from pathlib import Path


class PromptLoader:
    def __init__(self, prompt_dir: Path = Path("app/prompts")):
        self.prompt_dir = prompt_dir

    def load(self, name: str) -> str:
        path = self.prompt_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Prompt not found: {path}")
        return path.read_text(encoding="utf-8")
