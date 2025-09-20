
FUNCTION_DECLARATIONS = {
    "generate_marketing_captions": {
        "description": "Generate marketing captions for a product",
        "parameters": {
            "type": "object",
            "properties": {
                "captions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "The main caption text"
                            },
                            "hashtags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Relevant hashtags for the post"
                            },
                            "emojis": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Relevant emojis for the post"
                            }
                        },
                        "required": ["text", "hashtags", "emojis"]
                    },
                    "minItems": 3,
                    "maxItems": 3
                }
            },
            "required": ["captions"]
        }
    }
}
