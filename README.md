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
