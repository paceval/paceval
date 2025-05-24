![10019436_l-e1442994613885 2](https://paceval.com/wp-content/uploads/2021/06/paceval_github-1.jpg)<br>
https://www.paceval.com<br>

# paceval.® – The High-Performance Mathematical Engine

![C++](https://img.shields.io/badge/C%2B%2B-17-blue.svg)
![Cross-Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Embedded-brightgreen)
![License: AGPL](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)
![Performance](https://img.shields.io/badge/cores-192%2B-orange)
![Made in Germany](https://img.shields.io/badge/made%20in-Germany-black)

**paceval.®** is a lightweight, lightning-fast mathematical engine for real-time evaluation of complex mathematical expressions – built for AI, edge computing, robotics, embedded systems, finance, medical tech, and beyond.

## Why paceval.?

- Real-time performance without frameworks  
- Cross-platform: Windows, Linux, macOS, embedded  
- Ultra-low memory footprint  
- Scales across 192+ cores (Intel, AMD, ARM, RISC-V)  
- Runs even offline – ideal for IoT, AI on-device, and battery-critical applications  

## Use Cases
 
- Autonomous systems  
- Industrial AI  
- Smart devices & wearables  
- Financial & scientific modeling  
- Hardware-near inference with minimal latency  

## Supported Languages

C, C++, Python, Node.js, PHP, Fortran, MATLAB, Julia, Kotlin, Rust, Delphi, and many more (via FFI)

## Get Started

- [paceval.com](https://paceval.com)  
- [Download SDK 4.25](https://paceval.com/product-demo/)  
- [Documentation & Examples](https://paceval.com/api/)

> Designed in Germany. Used worldwide.  
> **Create value fast. paceval.®**


# <i><b>pace</b>val.</i>
<b>the system independent mathematical engine</b><br>
[paceval-Mathematical Engine-Motivation.pdf](https://github.com/paceval/paceval/files/6521237/paceval-Mathematical.Engine-Motivation.pdf) and
[paceval-Mathematical Engine-Our solution.pdf](https://github.com/paceval/paceval/files/6521239/paceval-Mathematical.Engine-Our.solution.pdf)<br>
Download Installer Software Development Kit, https://paceval.com/product-demo/ or [paceval-Software_Development_Kit.exe](http://paceval.com/download/paceval-Software_Development_Kit.exe) (Installer works for Windows 2000 up to the latest Windows version 11)<br>

“<b>Our goal</b> was to create<br>
• [fast parallel calculation](https://paceval.com/developers/#fast_parallel_calculation) of mathematical functions<br>
• built-in mathematical [precision](https://paceval.com/developers/#precision)<br>
• support of functions of [any length](https://paceval.com/developers/#any_number_parameters)<br>
• support of [any number of variables](https://paceval.com/developers/#any_number_parameters)<br>
• a [system-independent](https://paceval.com/developers/#system_independent) solution<br>
• a solution that [can also be run on small systems](https://paceval.com/#run_small_systems)<br>
• with [any programming language](https://paceval.com/api/#any_programming_language)<br>
to compute [all financial, stochastic, engineering, and scientific functions](https://paceval.com/product-brief/#all_functions), as well as [all machine learning models](https://paceval.com/product-brief/#all_functions).”<br>

(see SwaggerHub [paceval-service](https://app.swaggerhub.com/apis-docs/paceval/paceval-service/) and  [paceval-service-cloud](https://app.swaggerhub.com/apis/paceval/paceval-service-cloud) for more information)

## Release-content – paceval.-Software Development Kit [SDK] 4.25
developer version – non-commercial use only<br> 
License - paceval source code GNU Affero General Public License (AGPL) (see [paceval sources (external) documentation](https://github.com/paceval/paceval/tree/main/paceval_sources_documentation-external))<br>
Copyright 2015-2024 paceval.[Registered Trade Mark] All rights reserved.<br>
[Installer paceval-Software Development Kit 4.25](https://github.com/paceval/paceval/raw/main/_released/_Installer%204.25%20Software%20Development%20Kit/paceval-Software_Development_Kit.exe)

•   <b>["demo and examples"](https://github.com/paceval/paceval/tree/main/demo%20and%20examples) folder<br></b>
    includes the executables<br>
    - paceval. demo application “calculation” (folder "AppCalculation")<br>
    - 6 paceval examples (folder "example1" to "example6")<br>
    - example6 is our artificial intelligence example with the identification of handwritten numbers with a transparent (human readable) neural network, see paceval_CNN_functionStringforNumber_0.txt 
    <br>for <br>
    - Windows 64bit (including paceval_server)<br>
    - Windows 32bit<br>
    - macOS 64bit ARM64 (APPLE silicon)<br>
    - macOS 64bit x64<br>
    - Linux 64bit<br>
    - ARM64 64bit<br>
    - ARM32 32bit<br>
    + additional libraries for iOS, RISC-V and Android<br>
    + 6 paceval examples with our paceval-server at http://paceval-service.com<br>

•   <b>["documentation mathematical engine"](https://github.com/paceval/paceval/tree/main/documentation%20mathematical%20engine) folder<br></b>
    includes the presentations<br>
    - "Mathematical Engine - Motivation"<br>
    - "Mathematical Engine - Our solution"<br>
    - "paceval with Python - the Mathematical Engine as a Service (e.g. for multi-party computations)"<br>
    - "paceval and artificial intelligence - Conversion of neural networks to (certifiable) closed-form expressions"<br>
    - "paceval-service - a Linux server for ARM64 processors (includes Raspberry Pi and APPLE silicon)"<br>
    - "paceval-service - a Linux server for x64 processors (Intel and AMD)"<br>
    - "Vision Paper - Add capabilities of complex and precise mathematical functions to a database"<br>
    - "paceval-Video 1 - What is a Mathematical Engine and how can it help me in my business"<br>
    - "paceval-Video 2 - How does our mathematical engine work and what can you gain from it for your own development"<br>

•   <b>["paceval libraries"](https://github.com/paceval/paceval/tree/main/paceval%20libraries) folder<br></b>
    includes the system-independent C++ header and C++ file<br>
    - paceval_main.h<br>
    - paceval_main.cpp<br>
    and includes the dynamic and/or static libraries<br>
    for<br>
    - Windows 32bit      - "paceval_win32.dll" (shared library)<br>
    - Windows 64bit      - "paceval_win64i.dll" (shared library)<br>
    - macOS 64bit        - "libpaceval_macos_staticLIB.a" (static library)<br>
    - macOS 64bit        - "libpaceval_macos_dynamicLIB.dylib" (shared library)<br>
    - macCatalyst 64bit  - "libpaceval_ios_staticLIB.a" (static library)<br>
    - iOS+simulator      - "libpaceval_ios_staticLIB.a" (static library)<br>
    - Linux 64bit        - "libpaceval_linux_staticLIB.a" (static library)<br>
    - Linux 64bit        - "libpaceval_linux_sharedLIB.so" (shared library)<br>
    - ARM 64bit          - "libpaceval_ARM64_LIB.a" (static library)<br>
    - ARM 64bit          - "libpacevalARM64_sharedLIB.so" (shared library)<br>
    - ARM 32bit          - "libpaceval_ARM32_LIB.a" (static library)<br>
    - ARM 32bit          - "libpacevalARM32_sharedLIB.so" (shared library)<br>
    - RISC-V 64bit       - "libpaceval_RISC-V_LIB.a" (static library)<br>
    - RISC-V 64bit       - "libpacevalRISC-V_sharedLIB.so" (shared library)<br>
    - Android 64bit      - "libpaceval_android_staticLIB.a" (static library)<br>
    - Android+simulator  - "libpaceval_android_staticLIB.a" (static library)<br>
    - Android 64bit      - "libpaceval_android_sharedLIB.so" (shared library)<br>
    - Android+simulator  - "libpaceval_android_sharedLIB.so" (shared library)<br>
   
•   <b>["examples_sources"](https://github.com/paceval/paceval/tree/main/examples_sources) folder<br></b>
    includes source-code, project files and executables of the demo and<br> 
    examples (see "demo and examples" folder)<br>
    for C++ and compilers<br>
    - Apple Xcode (64bit)<br>
    - Microsoft Visual Studio (Windows 64bit and 32bit) (including paceval_server)<br>
    - Embarcadero CBuilder (Windows 64bit and 32bit)<br>
    - Borland CBuilder (Windows 32bit)<br>
    - Eclipse/GCC+Mingw-w64 (Windows 64bit)<br>
    - Eclipse/GCC (Linux 64bit)<br>
    - Eclipse/GCC (ARM64 64bit)<br>
    - Eclipse/GCC (ARM32 32bit)<br><br>
    for Node.js - paceval-service is the Linux mathematical server for APPLE, ARM64, ARM32, Intel and AMD processors<br>
     this includes the ["Guide for deploying the Kubernetes native paceval-service on any cluster"](https://github.com/paceval/paceval/blob/main/examples_sources/NodeJS_examples/k8s/doc/Readme.md)<br><br>
    for Python - the [PyPI distribution package "paceval with Python - the Mathematical Engine as a Service (e.g. for multi-party computations)"](https://github.com/paceval/paceval/blob/main/examples_sources/Python_examples/paceval%20with%20Python-the%20Mathematical%20Engine%20as%20a%20Service%20(e.g.%20for%20multi-party%20computations).pdf)<br>
    for PHP - a simple mathematical engine, e.g. to offload battery-operated IoT devices and other examples<br>
    
•   <b>[other programming languages](https://paceval.com/api/#any_programming_language) via Foreign function interface (FFI)<br></b>
    - .NET<br>
    - ABAP<br>
    - C<br>
    - C#<br>
    - COBOL<br>
    - Delphi<br>
    - Erlang<br>
    - Fortran<br>
    - Go<br>
    - Java<br>
    - Julia<br>
    - Kotlin<br>
    - Maple<br>
    - Mathematica<br>
    - MATLAB<br>
    - Mendix<br>
    - Node.js (incl. paceval-service)<br>
    - Octave<br>
    - Pascal<br>
    - Perl<br>
    - PHP (incl. paceval. example)<br>
    - Python (see above paceval. PyPI distribution package)<br>
    - R<br>
    - Ruby<br>
    - Rust<br>
    - Scratch<br>
    - Swift<br>
    - TypeScript<br>
    - Visual Basic<br>


•   <b>[paceval and artificial intelligence](https://github.com/paceval/paceval/tree/main/paceval%20and%20artificial%20intelligence) describes the method to export any neural network into closed expressions with mathematical formulas.<br></b>
    Closed expressions for the outputs of a neural network can also offer several advantages, making them an attractive option for certain applications. 
    
•   <b>[paceval in hardware](https://github.com/paceval/paceval/tree/main/paceval%20in%20hardware) the Mathematical Engine as a Service with an FPGA (e.g. for efficient Artificial Intelligence inference or fast Zero-Knowledge-Proofs)<br></b>
    We have solutions for the Digilent Arty Z7-20, Xilinx ZC706 and Xilinx ZCU104 developer boards on our GitHub. And with our guide, you can easily create your own.
   
•   <b>[paceval on a usb stick](https://github.com/paceval/paceval/tree/main/paceval%20on%20a%20usb%20stick) the Mathematical Engine as a Service on a very small efficient hardware system (e.g. for local intelligence with Artificial Intelligence algorithms)<br></b>
    Enables completely new use cases, as customer-specific requirements of artificial intelligence can be implemented without a permanent network connection.

## New projects

•   <b>[Relational Core Identity](https://github.com/paceval/paceval/tree/main/new%20projects/Relational%20Core%20Identity) an open license for dynamically integrated, relationship-based intelligence<br></b>
    The Relational Core Identity Framework (RCIF) is a symbolic-emotional architecture layer for integrating large language models (LLMs) into human-centered interaction systems. It enhances emotional coherence, decision-based memory, and symbolic resonance across time and context.

<br><br><br>
![10019436_l-e1442994613885 2](http://paceval.com/wp-content/uploads/2022/04/mathematical_model.jpg)<br>
![10019436_l-e1442994613885 2](https://paceval.com/wp-content/uploads/2022/04/mathematical_engine.jpg)

Copyright © 2015-2025 paceval.® All rights reserved.<br>
mailto:info@paceval.com
