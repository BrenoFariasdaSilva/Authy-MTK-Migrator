<div align="center">
  
# [Authy-MTK-Migrator.](https://github.com/BrenoFariasdaSilva/Authy-MTK-Migrator) <img src="https://github.com/BrenoFariasdaSilva/Authy-MTK-Migrator/blob/d4173c3b2249a77b6b1a223b86e801ea2042eddc/.assets/Icons/GitHub%20Colored%20Icon.svg"  width="3%" height="3%">

</div>

<div align="center">
  
---

Offline recovery and migration of Authy two-factor authentication (2FA) tokens from compatible legacy MediaTek Android devices, with exports to Aegis, Proton Authenticator, `otpauth://` URIs, and QR codes.
  
---

</div>

<div align="center">

![GitHub Code Size in Bytes](https://img.shields.io/github/languages/code-size/BrenoFariasdaSilva/Authy-MTK-Migrator)
![GitHub Commits](https://img.shields.io/github/commit-activity/t/BrenoFariasdaSilva/Authy-MTK-Migrator/main)
![GitHub Last Commit](https://img.shields.io/github/last-commit/BrenoFariasdaSilva/Authy-MTK-Migrator)
![GitHub Forks](https://img.shields.io/github/forks/BrenoFariasdaSilva/Authy-MTK-Migrator)
![GitHub Language Count](https://img.shields.io/github/languages/count/BrenoFariasdaSilva/Authy-MTK-Migrator)
![GitHub License](https://img.shields.io/github/license/BrenoFariasdaSilva/Authy-MTK-Migrator)
![GitHub Stars](https://img.shields.io/github/stars/BrenoFariasdaSilva/Authy-MTK-Migrator)
![GitHub Contributors](https://img.shields.io/github/contributors/BrenoFariasdaSilva/Authy-MTK-Migrator)
![GitHub Created At](https://img.shields.io/github/created-at/BrenoFariasdaSilva/Authy-MTK-Migrator)
![wakatime](https://wakatime.com/badge/github/BrenoFariasdaSilva/Authy-MTK-Migrator.svg)
[![Open Issues](https://img.shields.io/github/issues/BrenoFariasdaSilva/Authy-MTK-Migrator)](https://github.com/BrenoFariasdaSilva/Authy-MTK-Migrator/issues)
[![Closed Issues](https://img.shields.io/github/issues-closed/BrenoFariasdaSilva/Authy-MTK-Migrator)](https://github.com/BrenoFariasdaSilva/Authy-MTK-Migrator/issues?q=is%3Aissue+is%3Aclosed)
[![Open Pull Requests](https://img.shields.io/github/issues-pr/BrenoFariasdaSilva/Authy-MTK-Migrator)](https://github.com/BrenoFariasdaSilva/Authy-MTK-Migrator/pulls)
[![Closed Pull Requests](https://img.shields.io/github/issues-pr-closed/BrenoFariasdaSilva/Authy-MTK-Migrator)](https://github.com/BrenoFariasdaSilva/Authy-MTK-Migrator/pulls?q=is%3Apr+is%3Aclosed)
[![Monthly Commits](https://img.shields.io/github/commit-activity/m/BrenoFariasdaSilva/Authy-MTK-Migrator/main)](https://github.com/BrenoFariasdaSilva/Authy-MTK-Migrator/commits)
[![Merged PRs](https://img.shields.io/github/issues-search/BrenoFariasdaSilva/Authy-MTK-Migrator?query=is%3Apr%20is%3Amerged&label=merged%20PRs&color=blue)](https://github.com/BrenoFariasdaSilva/Authy-MTK-Migrator/pulls?q=is%3Apr+is%3Amerged)
![Purpose](https://img.shields.io/badge/Purpose-Authy%20Token%20Migration-6f42c1)
![Workflow](https://img.shields.io/badge/Workflow-Conventional%20Commits-227c4a)
![Repobeats Statistics](https://repobeats.axiom.co/api/embed/ac647e4939b05c18ec875dbf58df9306d1f697eb.svg)

</div>

## Table of Contents
- [Authy-MTK-Migrator. ](#authy-mtk-migrator-)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Requirements](#requirements)
  - [Setup](#setup)
    - [Clone the repository](#clone-the-repository)
  - [Installation:](#installation)
  - [Run Programing Language Code:](#run-programing-language-code)
    - [Dependencies](#dependencies)
    - [Dataset - Optional](#dataset---optional)
  - [Usage](#usage)
  - [Results - Optional](#results---optional)
  - [How to Cite?](#how-to-cite)
  - [Contributing](#contributing)
  - [Collaborators](#collaborators)
  - [License](#license)
    - [Apache License 2.0](#apache-license-20)

## Introduction

Authy-MTK-Migrator is an offline Python toolkit for recovering Authy OTP secrets from **owned, compatible older MediaTek Android devices** and converting those secrets into portable formats for other authenticator applications. The recovery workflow uses [MTKClient](https://github.com/bkerler/mtkclient) to read the device's `userdata` partition, `debugfs` to extract Authy's shared-preferences XML from an **unencrypted ext2/3/4 filesystem**, and local parsers to prepare exports for Aegis, Proton Authenticator, standard OTP URI lists, or individual QR codes.

The toolkit also accepts compatible **already-extracted** Authy XML, decrypted JSON from [Authy-iOS-MiTM](https://github.com/BrenoFariasdaSilva/Authy-iOS-MiTM), and supported authenticator export files. These file-conversion features do **not** require a MediaTek device. The MediaTek-specific part is the automated device acquisition, which is **not** universal: modern encrypted Android devices, other chipsets, and unsupported firmware cannot be assumed to work. The tool cannot bypass Android encryption or access restrictions.

**Repository status (November 2026):** The working standalone prototype and its tests were prepared separately, but the Python implementation has **not yet been committed to this repository**. Commands below describe that prototype and will work in this repository only after its source files, dependencies, and scripts are added. Hardware acquisition and actual imports into destination apps have not been validated on a physical device.

## Requirements

- **Python 3.11+** for the standalone converter, plus its Python dependencies (`cryptography`, `Pillow`, and `qrcode`).
- **macOS or Linux** recommended for MediaTek acquisition, with Git, libusb, and a separately installed [MTKClient](https://github.com/bkerler/mtkclient). On macOS, Homebrew can install the required host tools.
- **`e2fsprogs` / `debugfs`** to read a supported, unencrypted ext2/3/4 `userdata` image.
- **An owned or explicitly authorized MediaTek device**, with accessible BROM/preloader, readable unencrypted `userdata`, and Authy previously signed in with the relevant tokens, **or** a compatible local XML/JSON/OTP URI file for file-only conversion.
- **Enough free storage** for a complete `userdata` image if dumping a device, plus local export files.
- **The Authy backup password**, if some records contain encrypted secrets; this is different from the Authy app-lock PIN.

The hardware-dependent workflow is experimental. Merely having a MediaTek chipset does not guarantee that USB acquisition, filesystem extraction, or token recovery will succeed.

## Setup

### Clone the repository

1. Clone the repository with the following command:

   ```bash
   git clone https://github.com/BrenoFariasdaSilva/Authy-MTK-Migrator.git
   cd Authy-MTK-Migrator
   ```

## Installation:

* Python 3.11+ (after the standalone implementation files have been added to this repository):

  * Manually:
      ```bash
      python3 -m venv .venv
      source .venv/bin/activate
      python -m pip install -r requirements.txt
      ```

  * Using Makefile:
      ```bash
      make setup
      ```

  * Using ShellScript (macOS with Homebrew; prepares Python and MTKClient):
      ```bash
      bash scripts/setup_macos.sh
      source .venv/bin/activate
      ```  

  The prototype's setup script checks for prerequisites and installs MTKClient in a separate virtual environment. No setup script is necessary for converting an already-extracted supported file once Python dependencies are installed. **The `Makefile` and setup script are not yet available in the current GitHub checkout.**

## Run Programing Language Code:

```bash
# After installing the standalone prototype:
python -m android_mtk doctor
python -m android_mtk --help
```

### Dependencies

1. Install the prototype's Python dependencies (after `requirements.txt` has been committed) with the following command:

   ```bash
   python -m pip install -r requirements.txt
   ```

   The reference prototype pins `cryptography`, `Pillow`, and `qrcode`. Hardware acquisition also requires MTKClient and its separately managed dependencies.

### Dataset - Optional

1. **No dataset download is required.** The tool processes an existing Authy XML/JSON/URI file or, on compatible hardware, a locally extracted `userdata` image. No `make dataset` target exists in the prototype. The unit tests use synthetic token records; never publish real 2FA secrets as test fixtures.

## Usage

Once the standalone prototype has been added and installed, you can convert an existing Authy XML file without connecting a device:

```bash
python -m android_mtk convert \
  --input ./com.authy.storage.tokens.authenticator.xml \
  --out ./exports \
  --formats aegis,proton,uris,qr \
  --acknowledge-secrets
```

For an **owned, supported, unencrypted legacy MediaTek device**, the prototype supports an interactive acquisition-to-export workflow:

```bash
umask 077
python -m android_mtk recover \
  --mtk-dir .tools/mtkclient \
  --mtk-python .tools/mtkclient/.venv/bin/python \
  --out ./authy-recovery \
  --owned-device --acknowledge-secrets --formats all
```

Connect the powered-off device in its **device-specific** BROM/preloader mode when prompted by MTKClient; the key combination is not universal. Other prototype commands include `dump`, `extract`, `verify`, `backup`, and `restore-backup`. The `recover` command does not overwrite raw device images or modify device partitions, and the export step does not import tokens into another app automatically.

**Security:** `userdata.img`, extracted XML, export JSON, OTP URIs, and QR codes may contain live 2FA credentials. Store them locally with restricted access, never publish them, and **verify every account in the destination app before removing Authy**. Authy-specific 7-digit codes with 10-second periods may not work in all other apps. See the [original November 2026 method](https://gist.github.com/gboudreau/94bb0c11a6209c82418d01a59d958c93) for the hardware context.

## Results - Optional

The separate standalone Python prototype passed **20/20 synthetic unit tests**, covering token parsing, supported Authy decryption, OTP properties, export formats, encrypted backups, and mocked read-only MediaTek command execution. Run the tests after the prototype source files have been added:

```bash
python -m unittest discover -s tests -p test_android_mtk.py -v
```

**Limitations:** No physical MediaTek device was used in these tests, and no successful import inside Aegis, Proton Authenticator, or other destination apps was independently verified. The reported **MT8321 / Android 7.0** recovery was performed by the [original gist author](https://gist.github.com/gboudreau/94bb0c11a6209c82418d01a59d958c93), not by this project's prototype tests.

## How to Cite?

If you use the Authy-MTK-Migrator in your research, please cite it using the following BibTeX entry:

```
@misc{softwareAuthy-MTK-Migrator:2026,
  title = {Authy-MTK-Migrator: Automated offline Authy token recovery from legacy MediaTek Android devices, with exports to Aegis, Proton Authenticator, OTP URIs, and QR codes.},
  author = {Breno Farias da Silva},
  year = {2026},
  howpublished = {https://github.com/BrenoFariasdaSilva/Authy-MTK-Migrator},
  note = {Accessed on November 22, 2026}
}
```

Additionally, a `main.bib` file is available in the root directory of this repository, in which contains the BibTeX entry for this project.

If you find this repository valuable, please don't forget to give it a ⭐ to show your support! Contributions are highly encouraged, whether by creating issues for feedback or submitting pull requests (PRs) to improve the project. For details on how to contribute, please refer to the [Contributing](#contributing) section below.

Thank you for your support and for recognizing the contribution of this tool to your work!

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

Please follow the guidelines below or read [CONTRIBUTING.md](CONTRIBUTING.md) for detailed instructions.

1. **Set Up Your Environment:** Follow the [Setup](#setup) instructions.

2. **Make Your Changes:**
   - **Create a Branch:** `git checkout -b feature/YourFeatureName`
   - **Implement and Test:** Ensure your changes work correctly.
   - **Commit Your Changes:** Follow the [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) specification:

     ```text
     <type>[optional scope][!]: <description>
     ```

     Examples:
     - Features: `git commit -m "feat(export): add authenticator export format"`
     - Bug fixes: `git commit -m "fix(parser): reject malformed Authy token entries"`
     - Documentation: `git commit -m "docs(readme): update installation instructions"`
     - Refactoring: `git commit -m "refactor(recovery): separate device and file workflows"`
     - Tests: `git commit -m "test(tokens): add OTP parsing test cases"`

     Use `!` or a `BREAKING CHANGE:` footer to indicate breaking changes. See [CONTRIBUTING.md](CONTRIBUTING.md) for the complete rules.

3. **Submit Your Contribution:**
   - Push your branch: `git push origin feature/YourFeatureName`
   - Open a pull request describing your changes and relevant tests.

4. **Stay Engaged:** Respond to review feedback and make any necessary adjustments.

5. **Celebrate:** Once your pull request is merged, your contribution becomes part of the project!

## Collaborators

We thank the following people who contributed to this project:

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/BrenoFariasdaSilva" title="Breno Farias da Silva on GitHub">
        <img src="https://github.com/BrenoFariasdaSilva.png" width="100px;" alt="My Profile Picture"/><br>
        <sub>
          <b>Breno Farias da Silva</b>
        </sub>
      </a>
    </td>
  </tr>
</table>

## License

### Apache License 2.0

This project is licensed under the [Apache License 2.0](LICENSE). This license permits use, modification, distribution, and sublicense of the code for both private and commercial purposes, provided that the original copyright notice and a disclaimer of warranty are included in all copies or substantial portions of the software. It also requires a clear attribution back to the original author(s) of the repository. For more details, see the [LICENSE](LICENSE) file in this repository.
