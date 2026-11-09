# Security Policy

## Reporting a vulnerability

Please do **not** report security vulnerabilities through public GitHub
issues, discussions, or pull requests.

Use GitHub's **private vulnerability reporting** for this repository:
open the **Security** tab → **Report a vulnerability**. This reaches the
maintainers directly and privately.

Please include as much of the following as you can:

- The affected `modelctl` version (`modelctl --version`) and install source
  (release tag or git revision).
- A minimal reproduction, including the relevant store/cache layout and
  command lines (`modelctl` output is helpful; redact tokens and hostnames).
- Which atomicity or validation guarantee you believe is violated
  (staging → publish → activate ordering, path containment, symlink handling,
  ref ownership, etc.).

## Supported versions

Only the latest tagged release (`BlasterSystems/modelctl@vX.Y.Z`) receives
security fixes. The `0.x` series ships new functionality in minor releases;
security fixes may land as patch releases.

## Scope notes

`modelctl` generates inference-server commands but never starts servers, and
it validates all untrusted manifest values, repository paths, and resolved
references before filesystem use. Reports about *deployed* infrastructure
(NAS mounts, SSH hosts, inference runtimes) are out of scope here unless they
are caused by `modelctl` behavior itself.
