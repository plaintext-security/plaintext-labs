# Module 03 — File Systems & Carving

*Module concept · [Go to the hands-on lab →](lab.md)*


**Digital Forensics & IR** — *deleted files don't disappear — they just become invisible to the OS, and visible to you.*

## Why this matters
When a user deletes a file or an attacker wipes their traces, the operating system marks that space as available — but the data usually remains on disk until overwritten. File system forensics is the discipline of reading what's really on the media, not what the OS presents. It is where evidence goes after it's been "deleted" and where malware that never ran from a normal path often hides. Understanding how NTFS and ext4 actually allocate and reclaim space is what separates an investigator who can say "I found a deleted file" from one who can prove *when it was deleted, who deleted it, and what it contained*.

## Objective
Use SleuthKit tools (`fls`, `icat`, `fsstat`) to parse a raw disk image and recover deleted file entries; use `foremost` to carve recovered content from unallocated space; document the inodes and file paths that prove a file's existence and deletion.

## The core idea
Every filesystem is a data structure — a tree of metadata (inodes, MFT entries, directory entries) that points to clusters of actual file content. When a file is deleted, only the metadata pointer is removed from the directory listing. The MFT entry (NTFS) or inode (ext) is marked as unallocated, but the content clusters remain physically on disk until the allocator reuses them. This gap — between "metadata says deleted" and "data overwrote those sectors" — is the investigator's window. SleuthKit exploits it: `fls` lists *all* directory entries including deleted ones (flagged with `*`), and `icat` extracts the content at a given inode number even if the file no longer exists in the directory tree.

**The layer model** is the mental model that makes SleuthKit navigable. The Forensic Toolkit's five layers are: volume (partition table), filesystem (superblock, allocation tables), metadata (inode/MFT), filename (directory entries), and data (actual content clusters). Each SleuthKit tool operates at one layer: `mmls` at volume, `fsstat` at filesystem, `istat` at metadata, `fls` at filename, and `icat` at data. Knowing which layer you're querying tells you immediately what the output will and won't include. Most confusion about SleuthKit comes from mixing layers — asking `fls` for inode details, or expecting `icat` to know about filenames.

**File carving** is a different and complementary technique: instead of navigating the filesystem metadata, you scan the raw byte stream looking for known file signatures (magic bytes) and carve the data into a file regardless of whether any metadata exists for it. `foremost` uses a configuration file of header/footer byte patterns (PNG: `\x89PNG\r\n\x1a\n`; JPEG: `\xff\xd8\xff`; ZIP: `PK\x03\x04`) to locate and extract file-shaped content from unallocated space. Carving finds things the filesystem doesn't know about anymore, but it can't tell you the original filename, creation time, or path — the metadata is gone, only the content remains. You need both approaches: inode-based recovery when the metadata still exists, carving when it doesn't.

**NTFS is particularly artifact-rich** relative to other filesystems. The Master File Table (MFT) is a structured database where every file and directory, current and recently deleted, has an entry. Each MFT entry carries multiple attribute streams — `$DATA` for content, `$STANDARD_INFORMATION` for timestamps, `$FILE_NAME` for the filename-level timestamps (which differ from `$SI` timestamps and matter for timestomping detection, covered in Module 11). `$MFT` itself is a file you can extract and parse. NTFS also keeps transaction logs (`$LogFile`, `$UsnJrnl`) that record file system operations — a gold mine for reconstructing what happened, when, and in what order. SleuthKit reads MFT entries directly from the raw image, bypassing Windows entirely.

## Learn (~4 hrs)

**Filesystem internals (~1.5 hrs)**
- [Brian Carrier — File System Forensic Analysis (book overview)](https://www.amazon.com/System-Forensic-Analysis-Brian-Carrier/dp/0321268172) — the definitive text; if you have access, chapters 8–10 (FAT/NTFS) are the canonical reference. Otherwise, Carrier's tool documentation serves as a free proxy.
- [NTFS Documentation — ntfs.com](https://www.ntfs.com/ntfs-attributes.htm) — brief but precise on MFT attributes; understand `$DATA`, `$STANDARD_INFORMATION`, and `$FILE_NAME` before the lab.

**SleuthKit in practice (~1.5 hr)**
- [SleuthKit User Guide and Tool Documentation](https://sleuthkit.org/sleuthkit/docs/) — official reference for all SleuthKit tools (`fls`, `icat`, `fsstat`, `istat`, `mmls`); each tool's usage and output format. Keep this open during the lab.
- [foremost — SourceForge Project Documentation](https://foremost.sourceforge.net/) — the carver's documentation and configuration format; read the header/footer configuration section to understand how you'd add a new file type.

**FAT32 internals (for the lab image) (~1 hr)**
- [FAT32 File System Specification (Microsoft)](https://download.microsoft.com/download/1/6/1/161ba512-40e2-4cc9-843a-923143f3456c/fatgen103.doc) — the authoritative spec; sections 3–5 cover the FAT structure and directory entries. Worth a skim so you know what `fsstat` is reporting.

## Key concepts
- File deletion removes the directory entry and marks the inode/MFT entry unallocated; content sectors remain.
- SleuthKit's five-layer model: volume → filesystem → metadata → filename → data.
- `fls -d` lists deleted directory entries; `icat` extracts content at a given inode.
- File carving scans raw bytes for magic signatures; it recovers content without metadata.
- `foremost` uses a header/footer config to carve specific file types from unallocated space.
- NTFS MFT entries carry dual timestamps (`$SI` vs. `$FN`) that matter for anti-forensics detection.
- `$LogFile` and `$UsnJrnl` record filesystem operations — often more valuable than the files themselves.

## AI acceleration
AI is useful for translating SleuthKit command output into plain English ("what does this `fsstat` output tell me about the volume?") and for drafting foremost configuration entries for new file types. Where AI is not a substitute: it cannot read your disk image, and it will hallucinate inode numbers and specific offsets. Use it to explain the output you've already captured; always verify inode and offset values by running the tools yourself.
