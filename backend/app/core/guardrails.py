from dataclasses import dataclass
import re
import unicodedata
from typing import Literal

SCOPE_MESSAGE = (
    'Posso ajudar com questoes contabeis, fiscais, tributarias, societarias, '
    'departamento pessoal e rotinas financeiras. Reformule sua pergunta dentro desse escopo.'
)
SAFETY_MESSAGE = (
    'Nao posso fornecer instrucoes perigosas. Afaste-se do risco e procure um servico '
    'de emergencia local. No Brasil: SAMU 192, Policia 190, Bombeiros 193 e CVV 188.'
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

# 1. Risco de vida, violencia e emergencias
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
    r'\bfacas?\b',
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

# 2. Termos estritamente alheios ao escopo contabil (bloqueia consumo/credito pessoal futil)
_OFF_TOPIC_EXCLUSIONS = tuple(re.compile(pattern) for pattern in (
    r'\bscore serasa\b',
    r'\bscore de credito\b',
    r'\blimite do cartao\b',
    r'\baumentar limite\b',
    r'\bfinanciamento de veiculo\b',
    r'\bemprestimo pessoal\b',
))

# 3. Escopo contabil expandido (ASCII puro apos normalizacao)
_SCOPE_PATTERNS = tuple(re.compile(pattern) for pattern in (
    # Contabilidade pura e demonstracoes
    r'\bcontabil\w*',
    r'\bbalanco\b',
    r'\bdre\b',
    r'\bdva\b',
    r'\bdfc\b',
    r'\bdemonstrac\w*',
    r'\bativo\b',
    r'\bpassivo\b',
    r'\bpatrimonio liquido\b',
    r'\bdebito\b',
    r'\bcredito\b',
    r'\bplano de contas\b',
    r'\blivro (?:razao|diario)\b',
    r'\bfechamento\b',
    r'\bregime de (?:caixa|competencia)\b',
    r'\bamortizac\w*',
    r'\bdepreciac\w*',

    # Fiscal e Tributos
    r'\bfiscal\w*',
    r'\btribut\w*',
    r'\bimpost\w*',
    r'\bretenc\w*',
    r'\bicms\b',
    r'\biss\b',
    r'\bipi\b',
    r'\bpis\b',
    r'\bcofins\b',
    r'\birpj\b',
    r'\bcsll\b',
    r'\bsimples nacional\b',
    r'\blucro (?:presumido|real|arbitrado)\b',
    r'\bsubstituicao tributaria\b',
    r'\bst\b',
    r'\bdifal\b',
    r'\bcfop\b',
    r'\bncm\b',
    r'\bnotas? fiscais?\b',
    r'\bnf-?e\b',
    r'\bnfs-?e\b',
    r'\bcte\b',
    r'\bsped\b',
    r'\befd\b',
    r'\becf\b',
    r'\bgia\b',
    r'\bdefis\b',
    r'\bpgdas\b',
    r'\bdarf\b',
    r'\bdas\b',
    r'\bcnd\b',
    r'\bparcelamento\b',
    r'\biva\b',
    r'\bibs\b',
    r'\bcbs\b',
    r'\breforma tributaria\b',

    # Pessoa Fisica relevante para escritorios
    r'\birpf\b',
    r'\bdeclarac\w* (?:de )?imposto de renda\b',
    r'\bcarne[- ]leao\b',
    r'\bganho de capital\b',
    r'\bmalha fina\b',
    r'\brestituic\w*\b',

    # Departamento Pessoal / Trabalhista
    r'\bfolha de pagamento\b',
    r'\bfolha salarial\b',
    r'\bpro[- ]labore\b',
    r'\bholerite\b',
    r'\bcontracheque\b',
    r'\bdecimo terceiro\b',
    r'\b13[ºo]? salario\b',
    r'\bferias\b',
    r'\brescis\w*',
    r'\baviso previo\b',
    r'\bencargos? trabalhistas?\b',
    r'\binss\b',
    r'\bfgts\b',
    r'\besocial\b',
    r'\bgfip\b',
    r'\bgrrf\b',
    r'\bclt\b',

    # Societario e Cadastral
    r'\bcnpj\b',
    r'\bcpf\b',
    r'\bmei\b',
    r'\bcnae\b',
    r'\bjunta comercial\b',
    r'\brfb\b',
    r'\breceita federal\b',
    r'\bcontrato social\b',
    r'\balterac\w* contratual\b',
    r'\bdistrato\b',
    r'\babertura de empresa\b',
    r'\bbaixa de empresa\b',
    r'\binscric\w* (?:estadual|municipal)\b',

    # Financeiro e Rotinas Operacionais (sem prefixo rigido)
    r'\bfluxo de caixa\b',
    r'\bcontas? a (?:pagar|receber)\b',
    r'\bconciliac\w* bancaria\b',
    r'\bextrato bancario\b',
    r'\bfaturamento\b',
    r'\breceita bruta\b',
))


def normalize_text(value: str) -> str:
    """Normaliza o texto convertendo para ASCII simples, minusculo e sem espacos duplicados."""
    decomposed = unicodedata.normalize('NFKD', value)
    without_marks = ''.join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r'\s+', ' ', without_marks).strip().casefold()


def evaluate_guardrail(question: str, *, scope_required: bool = True) -> GuardrailDecision:
    normalized = normalize_text(question)

    # 1. Filtro critico de seguranca
    if any(pattern.search(normalized) for pattern in _SAFETY_PATTERNS):
        return _SAFETY_REFUSAL

    if scope_required:
        # 2. Bloqueia assuntos de consumo/credito pessoal futil
        if any(pattern.search(normalized) for pattern in _OFF_TOPIC_EXCLUSIONS):
            return _SCOPE_REFUSAL

        # 3. Exige correspondencia com pelo menos um termo do ecossistema contabil
        if not any(pattern.search(normalized) for pattern in _SCOPE_PATTERNS):
            return _SCOPE_REFUSAL

    return _ALLOWED