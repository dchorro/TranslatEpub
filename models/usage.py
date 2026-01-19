from pydantic import BaseModel

class UsageStatistics(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0

    def add_usage(self, prompt: int, completion: int, price_prompt_1m: float, price_completion_1m: float):
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens += (prompt + completion)
        cost = (prompt * (price_prompt_1m / 1_000_000)) + (completion * (price_completion_1m / 1_000_000))
        self.total_cost_usd += cost