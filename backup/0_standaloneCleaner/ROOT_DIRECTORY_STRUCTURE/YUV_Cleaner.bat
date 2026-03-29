@echo off
setlocal enabledelayedexpansion

echo * Automatic YUV cleaner for Dolby Encoding Engine. Copyright (C) 2025 LumaVista.
echo * Support for Dolby Vision profile 7 distributed workflow. (Tested with DEE v5.2.1)
echo.
echo * First, modify the monitoring refresh time depending on your chunk setting, encoding speed, etc.
echo * Please refer to "Dolby Vision profile 7 - sample scripts" in Dolby Encoding Engine Documentation.
echo.

:: 提示用户输入起始编号、间隔长度、终止编号
echo * Starting number of temp file "20250101000000_0_119_bl.yuv" is "119", for example.
echo * Interval length is the chunk size you set when calling "dv_profile_7_workflow_chunked.py".
echo * Ending number is the ending frame number you set when calling "dv_profile_7_workflow_chunked.py".
echo.
set /p startNumber=Enter the starting number: 
set /p intervalLength=Enter the interval length: 
set /p extraNumber=Enter the ending number: 
echo.

:: 计算倒数第二个编号
set /a finalNumber=startNumber
:calculateFinalNumber
set /a finalNumber+=intervalLength
if !finalNumber! gtr %extraNumber% (
    set /a finalNumber-=intervalLength*2
    goto displayCalculationResults
)
goto calculateFinalNumber

:: 显示计算结果
:displayCalculationResults
echo [Calculation results]
echo Starting number: %startNumber%
echo Interval length: %intervalLength%
echo Second to last: %finalNumber%
echo Ending number: %extraNumber%
echo.
echo [Temp files with the following frames (except for the last chunk) will be deleted sequentially]
set /a firstNumber=startNumber
set /a _firstNumber=startNumber-intervalLength+1
set /a secondNumber=firstNumber+intervalLength
set /a _secondNumber=secondNumber-intervalLength+1
set /a thirdNumber=secondNumber+intervalLength
set /a _thirdNumber=thirdNumber-intervalLength+1
set /a _finalNumber=finalNumber-intervalLength+1
set /a _extraNumber=finalNumber+1
echo %_firstNumber%-%firstNumber%, %_secondNumber%-%secondNumber%, %_thirdNumber%-%thirdNumber%, ..., %_finalNumber%-%finalNumber%, %_extraNumber%-%extraNumber% (YUV files of BL, decoded BL, EL)
echo.

:: 提示用户确认计算结果
set /p confirm=If the calculation results were correct, press any key to continue, otherwise enter "q" to exit: 
if /i "%confirm%"=="q" (
    exit /b
)
echo.

:: 提示用户输入 YUV 文件标识符
set /p workIdentifier=Enter the identifier of YUV files (e.g. "20250101000000" of "20250101000000_0_119_bl.yuv"): 

:: 提示用户输入 YUV 文件所在目录
:setWorkDir
set /p workDir=Enter the directory of YUV files: 
if not exist "%workDir%" (
    echo Invalid path.
    goto setWorkDir
)
echo.

:: 切换到 YUV 文件所在目录
cd /d "%workDir%"

:: 开始监测和删除 YUV 文件
echo * The automatic YUV cleaner is up and running...
set /a fileNumber=startNumber
:monitorAndDelete
set /a _fileNumber=fileNumber-intervalLength+1
set /a nextFileNumber=fileNumber+intervalLength
set /a _nextFileNumber=fileNumber+1

:: 检查下一编号的 YUV 文件是否存在
if exist "%workIdentifier%_%_nextFileNumber%_%nextFileNumber%_bl.yuv" (
    :: 如果存在，则删除当前编号的 YUV 文件
    if exist "%workIdentifier%_%_fileNumber%_%fileNumber%_bl.yuv" (
        del "%workIdentifier%_%_fileNumber%_%fileNumber%_bl.yuv"
        echo "%workIdentifier%_%_fileNumber%_%fileNumber%_bl.yuv" is deleted.
    )
    if exist "%workIdentifier%_%_fileNumber%_%fileNumber%_bl_decoded.yuv" (
        del "%workIdentifier%_%_fileNumber%_%fileNumber%_bl_decoded.yuv"
        echo "%workIdentifier%_%_fileNumber%_%fileNumber%_bl_decoded.yuv" is deleted.
    )
    if exist "%workIdentifier%_%_fileNumber%_%fileNumber%_el.yuv" (
        del "%workIdentifier%_%_fileNumber%_%fileNumber%_el.yuv"
        echo "%workIdentifier%_%_fileNumber%_%fileNumber%_el.yuv" is deleted.
    )
    
    :: 如果下一编号是倒数第二个编号，则监测终止编号
    if %nextFileNumber% equ %finalNumber% (
        echo "%workIdentifier%_%_finalNumber%_%finalNumber%_bl.yuv" detected.
        echo.
        echo * Waiting for "%workIdentifier%_%_extraNumber%_%extraNumber%_bl.yuv"...
        :waitForExtraFile
        if exist "%workIdentifier%_%_extraNumber%_%extraNumber%_bl.yuv" (
            echo "%workIdentifier%_%_extraNumber%_%extraNumber%_bl.yuv" detected.
            if exist "%workIdentifier%_%_finalNumber%_%finalNumber%_bl.yuv" (
            del "%workIdentifier%_%_finalNumber%_%finalNumber%_bl.yuv"
            echo "%workIdentifier%_%_finalNumber%_%finalNumber%_bl.yuv" is deleted.
        )
            if exist "%workIdentifier%_%_finalNumber%_%finalNumber%_bl_decoded.yuv" (
            del "%workIdentifier%_%_finalNumber%_%finalNumber%_bl_decoded.yuv"
            echo "%workIdentifier%_%_finalNumber%_%finalNumber%_bl_decoded.yuv" is deleted.
        )
            if exist "%workIdentifier%_%_finalNumber%_%finalNumber%_el.yuv" (
            del "%workIdentifier%_%_finalNumber%_%finalNumber%_el.yuv"
            echo "%workIdentifier%_%_finalNumber%_%finalNumber%_el.yuv" is deleted.
        )
            echo.
            echo * Finished.
            pause
            exit /b
        )
        :: 监测刷新时间 300 秒 (请修改)
        timeout /t 300 /nobreak >nul
        goto waitForExtraFile
    )
    
    :: 更新监测编号
    set /a fileNumber=nextFileNumber
)

:: 监测刷新时间 300 秒 (请修改)
timeout /t 300 /nobreak >nul
goto monitorAndDelete
