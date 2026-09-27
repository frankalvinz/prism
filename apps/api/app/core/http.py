import ssl

import truststore


def system_ssl_context() -> ssl.SSLContext:
    """Use OS trust store so local HTTPS-intercepting proxies/antivirus work."""
    return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
