from app.services.agno_client import AgnoAnswer, AgnoError, AgnoGeminiClient
from app.services.openai_client import OpenAIResponsesClient


class ProviderGateway:
    """Dispatches a request to the explicitly selected provider.

    There is intentionally no provider fallback: a failed OpenAI request must
    not silently send the prompt to Gemini (or vice versa).
    """

    async def query(
        self,
        *,
        provider: str,
        model_id: str,
        file_search_store_id: str | None,
        use_legacy_knowledge_base: bool = True,
        prompt: str,
        history: list[dict[str, str]],
        image: str | None = None,
        images: list[str] | None = None,
        image_bytes: bytes | None = None,
        image_format: str | None = None,
        image_bytes_list: list[bytes] | None = None,
        image_formats: list[str] | None = None,
        enable_web_search: bool = False,
        api_key: str | None = None,
    ) -> AgnoAnswer:
        if provider == 'gemini':
            return await AgnoGeminiClient().query(
                prompt=prompt,
                history=history,
                image=image,
                images=images,
                image_bytes=image_bytes,
                image_format=image_format,
                image_bytes_list=image_bytes_list,
                image_formats=image_formats,
                model_id=model_id,
                file_search_store_id=file_search_store_id,
                use_legacy_knowledge_base=use_legacy_knowledge_base,
                api_key=api_key,
            )
        if provider == 'openai':
            if file_search_store_id is not None:
                raise AgnoError(400, 'knowledge_base_provider_mismatch', 'Esta base de conhecimento só pode ser usada com Gemini.')
            return await OpenAIResponsesClient().query(
                prompt=prompt,
                history=history,
                model_id=model_id,
                image=image,
                images=images,
                image_bytes=image_bytes,
                image_format=image_format,
                image_bytes_list=image_bytes_list,
                image_formats=image_formats,
                enable_web_search=enable_web_search,
                api_key=api_key,
            )
        raise AgnoError(400, 'unsupported_provider', 'Provedor de IA não suportado.')


AIProviderGateway = ProviderGateway
