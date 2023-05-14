![10019436_l-e1442994613885 2](https://paceval.com/wp-content/uploads/2021/06/paceval_github-1.jpg)<br>

# <i><b>pace</b>val.</i>
<b>the system independent mathematical engine</b><br>
https://www.paceval.com<br>
[paceval-Mathematical Engine-Motivation.pdf](https://github.com/paceval/paceval/files/6521237/paceval-Mathematical.Engine-Motivation.pdf) and
[paceval-Mathematical Engine-Our solution.pdf](https://github.com/paceval/paceval/files/6521239/paceval-Mathematical.Engine-Our.solution.pdf)<br>
Download Installer Software Development Kit, https://paceval.com/product-demo/ or via Github [paceval-Software_Development_Kit.exe](http://paceval.com/download/paceval-Software_Development_Kit.exe) (Installer works for Windows 2000 up to the latest Windows version 11)<br>

“<b>Our goal</b> was to create<br>
• [fast parallel calculation](https://paceval.com/developers/#fast_parallel_calculation) of mathematical functions<br>
• built-in mathematical [precision](https://paceval.com/developers/#precision)<br>
• support of functions of [any length](https://paceval.com/developers/#any_number_parameters)<br>
• support of [any number of variables](https://paceval.com/developers/#any_number_parameters)<br>
• a [system-independent](https://paceval.com/developers/#system_independent) solution<br>
• a solution that [can also be run on small systems](https://paceval.com/#run_small_systems)<br>
• with [any programming language](https://paceval.com/api/#any_programming_language)<br>
to compute [all financial, stochastic, engineering, and scientific functions](https://paceval.com/product-brief/#all_functions), as well as [all machine learning models](https://paceval.com/product-brief/#all_functions).”<br>

(see [paceval at SwaggerHub](https://app.swaggerhub.com/apis-docs/paceval/paceval-service/4.04) for more information)

## Release-content – paceval.-Software Development Kit [SDK] 4.04a
developer version – non-commercial use only 

•   <b>["demo and examples"](https://github.com/paceval/paceval/tree/main/demo%20and%20examples) folder<br></b>
    includes the executables<br>
    - paceval. demo application “calculation” (folder "AppCalculation")<br>
    - 6 paceval examples (folder "example1" to "example6")<br>
    for <br>
    - Windows 64bit (including paceval_server)<br>
    - Windows 32bit<br>
    - macOS 64bit ARM64 (APPLE silicon)<br>
    - macOS 64bit x64<br>
    - Linux 64bit<br>
    - ARM64 64bit<br>
    - ARM32 32bit<br>
    - Android 64bit<br>

•   <b>["documentation mathematical engine"](https://github.com/paceval/paceval/tree/main/documentation%20mathematical%20engine) folder<br></b>
    includes the presentations<br>
    - "Mathematical Engine - Motivation"<br>
    - "Mathematical Engine - Our solution"<br>
    - "paceval-service - a Linux server for ARM64 processors (includes Raspberry Pi)"<br>
    - "paceval-service - a Linux server for x64 processors (Intel and AMD)"<br>
    - "Vision Paper - Add capabilities of complex and precise mathematical functions to a database"<br>

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
    - iOS+simulator      - "libpaceval_ios_staticLIB.a" (static library)<br>
    - Linux 64bit        - "libpaceval_linux_staticLIB.a" (static library)<br>
    - Linux 64bit        - "libpaceval_linux_sharedLIB.so" (shared library)<br>
    - ARM 64bit          - "libpaceval_ARM64_LIB.a" (static library)<br>
    - ARM 64bit          - "libpacevalARM64_sharedLIB.so" (shared library)<br>
    - ARM 32bit          - "libpaceval_ARM32_LIB.a" (static library)<br>
    - ARM 32bit          - "libpacevalARM32_sharedLIB.so" (shared library)<br>
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
    for Node.js - paceval-service is the Linux mathematical server for ARM64, Intel and AMD processors<br>
     this includes the ["Guide for deploying the Kubernetes native paceval-service on any cluster"](https://github.com/paceval/paceval/blob/main/examples_sources/NodeJS_examples/k8s/doc/Readme.md)<br><br>
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
    - Node.js<br>
    - Octave<br>
    - Pascal<br>
    - Perl<br>
    - PHP (incl. paceval. example)<br>
    - Python<br>
    - Ruby<br>
    - Rust<br>
    - Scratch<br>
    - Swift<br>
    - Visual Basic<br>

•   <b>[paceval in hardware](https://github.com/paceval/paceval/tree/main/paceval%20in%20hardware) the Mathematical Engine as a Service with an FPGA (e.g. for efficient Artificial Intelligence inference or fast Zero-Knowledge-Proofs)<br></b>
    We have solutions for the Digilent Arty Z7-20, Xilinx ZC706 and Xilinx ZCU104 developer boards on our GitHub. And with our guide, you can easily create your own.

![10019436_l-e1442994613885 2](http://paceval.com/wp-content/uploads/2022/04/mathematical_model.jpg)<br>
![10019436_l-e1442994613885 2](https://paceval.com/wp-content/uploads/2022/04/mathematical_engine.jpg)

Copyright © 2015-2023 paceval.® All rights reserved.<br>
mailto:info@paceval.com
