from __future__ import annotations

import json

from backend.services.rag_service import RAGService


if __name__ == "__main__":
    questions = [
        "ما هو الجلوكوما؟",
        "كيف أحجز موعد؟",
        "What does a high risk screening result mean?",
    ]

    service = RAGService()

    for question in questions:
        print("=" * 90)
        print("QUESTION:", question)
        result = service.answer(question)
        print("MODE:", result.get("mode"))
        print("ANSWER PREVIEW:")
        print(str(result.get("answer", ""))[:1200])
        print("SOURCES:")
        print(json.dumps(result.get("sources", []), ensure_ascii=False, indent=2))
