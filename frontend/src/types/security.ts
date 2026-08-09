export enum Algorithm {
  AES256_GCM = 'AES256_GCM',
  RSA4096 = 'RSA4096',
  ECC_P256 = 'ECC_P256',
  Ed25519 = 'Ed25519',
}

export enum KeyPurpose {
  ENCRYPTION = 'Encryption',
  SIGNATURE = 'Signature',
  VERIFICATION = 'Verification',
  WRAPPING = 'Wrapping',
}

export enum KeyStatus {
  ACTIVE = 'Active',
  INACTIVE = 'Inactive',
  EXPIRED = 'Expired',
  REVOKED = 'Revoked',
}

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
