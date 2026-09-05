export const Algorithm = {
  AES256_GCM: "AES256_GCM",
  RSA4096: "RSA4096",
  ECC_P256: "ECC_P256",
  Ed25519: "Ed25519",
} as const;

export type Algorithm = (typeof Algorithm)[keyof typeof Algorithm];

export const KeyPurpose = {
  Encryption: "Encryption",
  Signature: "Signature",
  Verification: "Verification",
  Wrapping: "Wrapping",
} as const;

export type KeyPurpose = (typeof KeyPurpose)[keyof typeof KeyPurpose];

export const KeyStatus = {
  Active: "Active",
  Inactive: "Inactive",
  Expired: "Expired",
  Revoked: "Revoked",
} as const;

export type KeyStatus = (typeof KeyStatus)[keyof typeof KeyStatus];

export interface KeyMetadata {
  id: string;
  key_identifier: string;
  algorithm: Algorithm;
  key_purpose: KeyPurpose;
  key_version: number;
  status: KeyStatus;
  expires_at?: string;
  activated_at?: string;
  deactivated_at?: string;
  rotation_due?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface GenerateKeyRequest {
  algorithm: Algorithm;
  key_purpose: KeyPurpose;
}
