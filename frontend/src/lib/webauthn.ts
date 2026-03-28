/**
 * Base64url encode/decode utilities for WebAuthn binary fields.
 */

export function base64urlEncode(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

export function base64urlDecode(str: string): ArrayBuffer {
  // Add padding
  let base64 = str.replace(/-/g, '+').replace(/_/g, '/')
  while (base64.length % 4 !== 0) {
    base64 += '='
  }
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return bytes.buffer
}

/**
 * Prepare PublicKeyCredentialCreationOptions from server JSON.
 * Converts base64url strings to ArrayBuffers where the WebAuthn API expects them.
 */
export function prepareRegistrationOptions(
  options: Record<string, unknown>
): PublicKeyCredentialCreationOptions {
  const publicKey = (options.publicKey ?? options) as Record<string, unknown>

  return {
    ...publicKey,
    challenge: base64urlDecode(publicKey.challenge as string),
    user: {
      ...(publicKey.user as Record<string, unknown>),
      id: base64urlDecode((publicKey.user as Record<string, string>).id),
    },
    excludeCredentials: ((publicKey.excludeCredentials as Array<Record<string, unknown>>) ?? []).map(
      (cred) => ({
        ...cred,
        id: base64urlDecode(cred.id as string),
      })
    ),
  } as PublicKeyCredentialCreationOptions
}

/**
 * Prepare PublicKeyCredentialRequestOptions from server JSON.
 */
export function prepareAuthenticationOptions(
  options: Record<string, unknown>
): PublicKeyCredentialRequestOptions {
  const publicKey = (options.publicKey ?? options) as Record<string, unknown>

  return {
    ...publicKey,
    challenge: base64urlDecode(publicKey.challenge as string),
    allowCredentials: ((publicKey.allowCredentials as Array<Record<string, unknown>>) ?? []).map(
      (cred) => ({
        ...cred,
        id: base64urlDecode(cred.id as string),
      })
    ),
  } as PublicKeyCredentialRequestOptions
}

/**
 * Serialize a registration credential response for sending to the server.
 */
export function serializeRegistrationCredential(
  credential: PublicKeyCredential
): Record<string, unknown> {
  const response = credential.response as AuthenticatorAttestationResponse
  return {
    id: credential.id,
    rawId: base64urlEncode(credential.rawId),
    type: credential.type,
    response: {
      attestationObject: base64urlEncode(response.attestationObject),
      clientDataJSON: base64urlEncode(response.clientDataJSON),
    },
    authenticatorAttachment: (credential as unknown as Record<string, string>).authenticatorAttachment,
  }
}

/**
 * Serialize an authentication credential response for sending to the server.
 */
export function serializeAuthenticationCredential(
  credential: PublicKeyCredential
): Record<string, unknown> {
  const response = credential.response as AuthenticatorAssertionResponse
  return {
    id: credential.id,
    rawId: base64urlEncode(credential.rawId),
    type: credential.type,
    response: {
      authenticatorData: base64urlEncode(response.authenticatorData),
      clientDataJSON: base64urlEncode(response.clientDataJSON),
      signature: base64urlEncode(response.signature),
      userHandle: response.userHandle ? base64urlEncode(response.userHandle) : null,
    },
  }
}
