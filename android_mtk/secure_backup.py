"""Optional password-encrypted offline backup of generated export files.

Format: magic + 16-byte salt + 12-byte nonce + AES-256-GCM ciphertext of ZIP.
Compatible with this project's `restore-backup` command, not an app-native file.
"""
