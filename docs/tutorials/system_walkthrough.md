# Tutorial: Full System Walkthrough

This guide provides a tour of the built-in applications and tools provided by the WebOS Framework. It demonstrates how different modules work together to create a unified OS experience.

## 1. The Dashboard (Launchpad)
When you first log in, you are greeted by the **Launchpad**. This is the "Start Menu" of WebOS.
- **App Grid**: Displays all registered modules (Blogger, File Explorer, Vault).
- **Search (HUD)**: Press `Ctrl+K` to open the Command Palette. You can jump directly to any app or system setting.

## 2. File Explorer (System Management)
The **File Explorer** is a dual-panel manager for the Abstract File System.
- **Local vs Remote**: You can browse files on the server's local disk alongside your S3/MinIO buckets.
- **Operations**: Upload, download, and move files between different storage backends using the Unified Storage API.

## 3. Blogger Portal (Content Management)
**Blogger** demonstrates a complex business module with tiered access.
- **Public Feed**: Guests can read published articles.
- **Private Editor**: Authenticated users can write posts using a rich-text editor.
- **Cross-Module Integration**: The Blog Editor integrates with the File Explorer via a "File Picker" to upload and insert images.

## 4. Personal Vault (Security)
The **Vault** is a password manager that demonstrates row-level data isolation.
- **Owned Documents**: Every secret you store is automatically protected by the `OwnedDocument` logic.
- **Zero Configuration**: A developer doesn't need to write custom "WHERE user_id = ?" queries; the framework handles it.

## 5. System Administration
The **Admin Dashboard** (available to superusers) provides tools to manage the entire ecosystem.
- **User Manager**: Add, edit, or deactivate users.
- **Module Inspector**: View all loaded modules and their status.
- **Settings Editor**: Real-time configuration of the system kernel (Log levels, API prefixes, etc.).

---

## 🚀 Ready to Build?
Now that you've seen what WebOS can do, head over to the [Create Your First Module](./create_module.md) tutorial to start building your own features!
