"""Safe local commands supported by Mini JARVIS."""

import ast
import operator
import re
from datetime import datetime


def detect_language(message: str) -> str:
    """Return Urdu for Urdu script or common Roman Urdu phrases, else English."""
    if re.search(r"[\u0600-\u06ff]", message):
        return "ur"
    roman_urdu = ("assalam", "ke bare", "batao", "kya", "hai", "kar do", "samjhao", "waqt")
    lowered = message.lower()
    return "ur" if any(term in lowered for term in roman_urdu) else "en"


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _safe_calculate(expression: str) -> float:
    """Evaluate arithmetic only; never evaluate names, calls, or Python code."""
    if len(expression) > 100:
        raise ValueError("That calculation is too long.")
    tree = ast.parse(expression, mode="eval")

    def visit(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 8:
                raise ValueError("Please use a smaller exponent.")
            return _BINARY_OPERATORS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
            return _UNARY_OPERATORS[type(node.op)](visit(node.operand))
        raise ValueError("I can only calculate basic arithmetic.")

    result = visit(tree)
    if abs(result) > 1e100:
        raise ValueError("That result is too large to display.")
    return result


def _calculation_expression(message: str) -> str | None:
    text = message.lower().replace(",", "")
    match = re.search(r"(?:calculate|what is|compute)\s+(.+?)[?.!]*$", text)
    expression = match.group(1) if match else text
    expression = re.sub(r"\b(multiplied by|times|x)\b", "*", expression)
    expression = re.sub(r"\b(divided by|over)\b", "/", expression)
    expression = re.sub(r"\b(plus|added to)\b", "+", expression)
    expression = re.sub(r"\b(minus|take away)\b", "-", expression)
    expression = re.sub(r"\b(point)\b", ".", expression)
    expression = re.sub(r"\b(and)\b", " ", expression)
    if not re.fullmatch(r"[\d\s.+*/()\-]+", expression.strip()):
        return None
    return expression.strip()


def handle_local_command(message: str, language: str) -> tuple[str, str] | None:
    """Handle exact safe command categories; return (reply, intent), or None."""
    text = message.lower().strip()
    if any(term in text for term in ("help", "what can you do", "your commands", "madad")):
        reply = (
            "I can answer questions, tell you the date and time, solve basic arithmetic, and search the web when configured."
            if language == "en"
            else "Main sawalon ke jawab, tareekh aur waqt, basic hisaab, aur key configure hone par web search kar sakta hoon."
        )
        return reply, "help"
    if any(term in text for term in ("hello", "hi jarvis", "hey jarvis", "assalam")) and len(text) < 100:
        return ("Wa alaikum assalam! How can I help you?" if language == "ur" else "Hello! How can I help you?"), "greeting"
    if any(term in text for term in ("time", "waqt")):
        now = datetime.now().astimezone().strftime("%I:%M %p")
        return (f"Abhi waqt {now} hai." if language == "ur" else f"The current time is {now}."), "time"
    if any(term in text for term in ("date", "today", "tareekh", "aaj")):
        today = datetime.now().astimezone().strftime("%A, %B %d, %Y")
        return (f"Aaj {today} hai." if language == "ur" else f"Today's date is {today}."), "date"
    expr = _calculation_expression(message)
    if expr:
        try:
            result = _safe_calculate(expr)
            shown = int(result) if result.is_integer() else result
            return (f"Jawab {shown} hai." if language == "ur" else f"The answer is {shown}."), "calculator"
        except (ValueError, ZeroDivisionError, SyntaxError):
            if any(word in text for word in ("calculate", "compute", "multiplied", "divided", "plus", "minus")):
                return ("Maaf kijiye, main yeh hisaab nahi kar saka." if language == "ur" else "Sorry, I couldn't calculate that. Please try a basic arithmetic expression."), "calculator"
    return None


def is_search_request(message: str) -> bool:
    text = message.lower()
    return any(term in text for term in ("search the web", "search online", "web search", "look up online", "latest news", "latest information"))


def extract_search_query(message: str) -> str:
    text = re.sub(r"^(please\s+)?(search( the web| online)?( for)?|look up online)\s*", "", message, flags=re.I)
    text = re.sub(r"\b(latest information about|latest news about)\b", "", text, flags=re.I)
    text = re.sub(r"\s+latest (news|information)\s*$", "", text, flags=re.I)
    return text.strip(" ?.!\n") or message.strip()
