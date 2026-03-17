from pydantic import BaseModel, Field

class ConstraintProblem(BaseModel):
    """Defines the input for the Constraint Problem."""
    input: str = Field(..., description="A description of a number of people and their relative height.")
    golden_label: str = Field(..., description="Expected output from the LLM e.g. ['Bob', 'Alice']")
