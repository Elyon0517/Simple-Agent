from google.genai import types


class ChatContextBuilder:
    def build_user_message(self, text: str) -> types.Content:
        return types.Content(
            role="user",
            parts=[types.Part(text=text)],
        )
