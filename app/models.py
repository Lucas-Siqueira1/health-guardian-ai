from pydantic import BaseModel, Field, field_validator

class QuestionarioProfissional(BaseModel):
    cargo: str = Field(
        description="Cargo do profissional de saúde"
    )
    setor: str = Field(
        description="Setor de trabalho do profissional"
    )
    turno: str = Field(
        description="Turno de trabalho atual"
    )
    horas_trabalhadas: float = Field(
        ge=1,
        le=24,
        description="Quantidade de horas trabalhadas no turno atual"
    )
    relato: str = Field(
        min_length=20,
        description="Relato do profissional sobre como está se sentindo"
    )

    @field_validator("cargo", "setor", "turno")
    @classmethod
    def validacao_vazio(cls, valor):
        if not valor.strip():
            raise ValueError("Este campo não pode estar vazio")
        return valor.strip()