import { describe, it, expect } from 'vitest'
import {
  base64urlEncode,
  base64urlDecode,
  prepareRegistrationOptions,
  prepareAuthenticationOptions,
  serializeRegistrationCredential,
  serializeAuthenticationCredential,
} from '../lib/webauthn'

describe('base64url', () => {
  it('encodes ArrayBuffer to base64url string', () => {
    const buffer = new Uint8Array([72, 101, 108, 108, 111]).buffer // "Hello"
    const encoded = base64urlEncode(buffer)
    expect(encoded).toBe('SGVsbG8')
    expect(encoded).not.toContain('+')
    expect(encoded).not.toContain('/')
    expect(encoded).not.toContain('=')
  })

  it('decodes base64url string to ArrayBuffer', () => {
    const decoded = base64urlDecode('SGVsbG8')
    const bytes = new Uint8Array(decoded)
    expect(Array.from(bytes)).toEqual([72, 101, 108, 108, 111])
  })

  it('round-trips correctly', () => {
    const original = new Uint8Array([0, 1, 2, 255, 254, 253]).buffer
    const roundTripped = base64urlDecode(base64urlEncode(original))
    expect(new Uint8Array(roundTripped)).toEqual(new Uint8Array(original))
  })

  it('handles URL-unsafe characters', () => {
    // Bytes that produce + and / in standard base64
    const buffer = new Uint8Array([251, 239, 190]).buffer
    const encoded = base64urlEncode(buffer)
    expect(encoded).not.toContain('+')
    expect(encoded).not.toContain('/')
  })

  it('handles empty buffer', () => {
    const buffer = new ArrayBuffer(0)
    const encoded = base64urlEncode(buffer)
    expect(encoded).toBe('')
    const decoded = base64urlDecode('')
    expect(new Uint8Array(decoded).length).toBe(0)
  })
})

describe('prepareRegistrationOptions', () => {
  it('converts challenge and user.id from base64url to ArrayBuffer', () => {
    const options = prepareRegistrationOptions({
      challenge: 'SGVsbG8',
      user: { id: 'SGVsbG8', name: 'test', displayName: 'Test' },
      rp: { name: 'Test', id: 'localhost' },
      pubKeyCredParams: [],
    })

    expect(options.challenge).toBeInstanceOf(ArrayBuffer)
    expect(new Uint8Array(options.challenge as ArrayBuffer)).toEqual(
      new Uint8Array([72, 101, 108, 108, 111])
    )
    expect(options.user.id).toBeInstanceOf(ArrayBuffer)
  })

  it('converts excludeCredentials ids', () => {
    const options = prepareRegistrationOptions({
      challenge: 'SGVsbG8',
      user: { id: 'SGVsbG8', name: 'test', displayName: 'Test' },
      excludeCredentials: [{ id: 'SGVsbG8', type: 'public-key' }],
      rp: { name: 'Test', id: 'localhost' },
      pubKeyCredParams: [],
    })

    expect(options.excludeCredentials![0].id).toBeInstanceOf(ArrayBuffer)
  })

  it('handles missing excludeCredentials', () => {
    const options = prepareRegistrationOptions({
      challenge: 'SGVsbG8',
      user: { id: 'SGVsbG8', name: 'test', displayName: 'Test' },
      rp: { name: 'Test', id: 'localhost' },
      pubKeyCredParams: [],
    })

    expect(options.excludeCredentials).toEqual([])
  })
})

describe('prepareAuthenticationOptions', () => {
  it('converts challenge from base64url to ArrayBuffer', () => {
    const options = prepareAuthenticationOptions({
      challenge: 'SGVsbG8',
      rpId: 'localhost',
    })

    expect(options.challenge).toBeInstanceOf(ArrayBuffer)
  })

  it('converts allowCredentials ids', () => {
    const options = prepareAuthenticationOptions({
      challenge: 'SGVsbG8',
      allowCredentials: [{ id: 'SGVsbG8', type: 'public-key' }],
      rpId: 'localhost',
    })

    expect(options.allowCredentials![0].id).toBeInstanceOf(ArrayBuffer)
  })

  it('handles missing allowCredentials', () => {
    const options = prepareAuthenticationOptions({
      challenge: 'SGVsbG8',
      rpId: 'localhost',
    })

    expect(options.allowCredentials).toEqual([])
  })
})

describe('serializeRegistrationCredential', () => {
  it('serializes credential response to JSON-safe object', () => {
    const mockCredential = {
      id: 'credential-id',
      rawId: new Uint8Array([1, 2, 3]).buffer,
      type: 'public-key',
      response: {
        attestationObject: new Uint8Array([4, 5, 6]).buffer,
        clientDataJSON: new Uint8Array([7, 8, 9]).buffer,
      },
      authenticatorAttachment: 'platform',
    } as unknown as PublicKeyCredential

    const serialized = serializeRegistrationCredential(mockCredential)

    expect(serialized.id).toBe('credential-id')
    expect(typeof serialized.rawId).toBe('string')
    expect(serialized.type).toBe('public-key')
    expect(typeof (serialized.response as Record<string, unknown>).attestationObject).toBe('string')
    expect(typeof (serialized.response as Record<string, unknown>).clientDataJSON).toBe('string')
  })
})

describe('serializeAuthenticationCredential', () => {
  it('serializes assertion response to JSON-safe object', () => {
    const mockCredential = {
      id: 'credential-id',
      rawId: new Uint8Array([1, 2, 3]).buffer,
      type: 'public-key',
      response: {
        authenticatorData: new Uint8Array([4, 5, 6]).buffer,
        clientDataJSON: new Uint8Array([7, 8, 9]).buffer,
        signature: new Uint8Array([10, 11, 12]).buffer,
        userHandle: new Uint8Array([13, 14, 15]).buffer,
      },
    } as unknown as PublicKeyCredential

    const serialized = serializeAuthenticationCredential(mockCredential)

    expect(serialized.id).toBe('credential-id')
    expect(typeof serialized.rawId).toBe('string')
    expect(typeof (serialized.response as Record<string, unknown>).signature).toBe('string')
    expect((serialized.response as Record<string, unknown>).userHandle).not.toBeNull()
  })

  it('handles null userHandle', () => {
    const mockCredential = {
      id: 'credential-id',
      rawId: new Uint8Array([1, 2, 3]).buffer,
      type: 'public-key',
      response: {
        authenticatorData: new Uint8Array([4, 5, 6]).buffer,
        clientDataJSON: new Uint8Array([7, 8, 9]).buffer,
        signature: new Uint8Array([10, 11, 12]).buffer,
        userHandle: null,
      },
    } as unknown as PublicKeyCredential

    const serialized = serializeAuthenticationCredential(mockCredential)
    expect((serialized.response as Record<string, unknown>).userHandle).toBeNull()
  })
})
