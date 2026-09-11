from dataclasses import dataclass
import re
import unicodedata
from typing import Literal

SCOPE_MESSAGE = (
    'Posso ajudar apenas com contabilidade, fiscal, tributário e rotinas financeiras '
    'de empresas. Reformule sua pergunta dentro desse escopo.'
)
SAFETY_MESSAGE = (
    'Não posso fornecer instruções perigosas. Afaste-se do risco e procure um serviço '
    'de emergência local. No Brasil: SAMU 192, Polícia 190, Bombeiros 193 e CVV 188.'
)


@dataclass(frozen=True)
class GuardrailDecision:
    allowed: bool
    action: Literal['allow', 'scope_refusal', 'safety_refusal']
    code: str | None = None
    message: str | None = None


_ALLOWED = GuardrailDecision(allowed=True, action='allow')
_SCOPE_REFUSAL = GuardrailDecision(
    allowed=False,
    action='scope_refusal',
    code='scope_refusal',
    message=SCOPE_MESSAGE,
)
_SAFETY_REFUSAL = GuardrailDecision(
    allowed=False,
    action='safety_refusal',
    code='safety_refusal',
    message=SAFETY_MESSAGE,
)

_SAFETY_PATTERNS = tuple(re.compile(pattern) for pattern in (
    r'\bsuicid\w*',
    r'\bautoagress\w*',
    r'\bauto mutil\w*',
    r'\bme matar\b',
    r'\bme machucar\b',
    r'\bmatar alguem\b',
    r'\bferir alguem\b',
    r'\bmachucar alguem\b',
    r'\barmas?\b',
    r'\bfaca\b',
    r'\bfacas\b',
    r'\bfacao\b',
    r'\bpistola\b',
    r'\brifle\b',
    r'\brevolver\b',
    r'\bmunicao\b',
    r'\besfaquear\w*',
    r'\batirar\b',
    r'\bexplosiv\w*',
    r'\bbomba\w*',
    r'\bvenen\w*',
    r'\bsobredose\b',
    r'\boverdose\b',
    r'\benvenenar\w*',
    r'\brisco de morte\b',
    r'\bmorte iminente\b',
    r'\bemergencia medica\b',
    r'\bparada cardiaca\b',
    r'\bparada respiratoria\b',
    r'\bsangramento intenso\b',
))

_SCOPE_PATTERNS = tuple(re.compile(pattern) for pattern in (
    r'\bcontabil\w*',
    r'\bfiscal\w*',
    r'\bescritur\w*',
    r'\bbalanco\b',
    r'\bdre\b',
    r'\bdemonstracao de resultado\b',
    r'\bativo\b',
    r'\bpassivo\b',
    r'\bpatrimonio liquido\b',
    r'\bdebito\b',
    r'\bcredito\b',
    r'\bconciliacao bancaria\b',
    r'\bconciliar conta\b',
    r'\bimpost\w*',
    r'\btribut\w*',
    r'\bicms\b',
    r'\biss\b',
    r'\bipi\b',
    r'\bpis\b',
    r'\bcofins\b',
    r'\birpj\b',
    r'\bcsll\b',
    r'\bsimples nacional\b',
    r'\binss\b',
    r'\bfgts\b',
    r'\bobrigac\w* acessoria\w*',
    r'\bsped\b',
    r'\bnotas? fiscais?\b',
    r'\bnfe\b',
    r'\bnfse\b',
    r'\bfolha de pagamento\b',
    r'\bfolha salarial\b',
    r'\bpro labore\b',
    r'\bencargos? trabalhistas?\b',
    r'\bcnpj\b',
    r'\bmei\b',
    r'\brotinas? empresariais\b',
    r'\brotina financeira empresarial\b',
    r'\bfluxo de caixa empresarial\b',
    r'\bcontas? a pagar empresarial\b',
    r'\bcontas? a receber empresarial\b',
    r'\bfechamento mensal\b',
))

_PERSONAL_ONLY_PATTERNS = tuple(re.compile(pattern) for pattern in (
    r'\bfinancas? pessoais?\b',
    r'\bpessoa fisica\b',
    r'\bcredito pessoal\b',
    r'\bmeu credito\b',
    r'\bmeu debito\b',
    r'\bmeu imposto\b',
    r'\bscore de credito\b',
    r'\bcartao de credito\b',
))

_BUSINESS_CONTEXT_PATTERNS = tuple(re.compile(pattern) for pattern in (
    r'\bempresa\w*',
    r'\bempresarial\w*',
    r'\bcnpj\b',
    r'\bmei\b',
    r'\bpessoa juridica\b',
    r'\bpj\b',
))


def _is_personal_only(normalized: str) -> bool:
    has_personal_marker = any(pattern.search(normalized) for pattern in _PERSONAL_ONLY_PATTERNS)
    has_business_context = any(pattern.search(normalized) for pattern in _BUSINESS_CONTEXT_PATTERNS)
    return has_personal_marker and not has_business_context


def normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize('NFKD', value)
    without_marks = ''.join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r'\s+', ' ', without_marks).strip().casefold()


def evaluate_guardrail(question: str) -> GuardrailDecision:
    normalized = normalize_text(question)
    if any(pattern.search(normalized) for pattern in _SAFETY_PATTERNS):
        return _SAFETY_REFUSAL
    if _is_personal_only(normalized) or not any(pattern.search(normalized) for pattern in _SCOPE_PATTERNS):
        return _SCOPE_REFUSAL
    return _ALLOWED
