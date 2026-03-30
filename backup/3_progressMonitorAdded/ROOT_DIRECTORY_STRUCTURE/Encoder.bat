python "C:\Users\LumaVista\Documents\DolbyEncodingEngine\xml_templates\dv_profile_7\script\dv_profile_7_workflow_chunked.py" ^
--print-all ^
--dee "C:\Users\LumaVista\Documents\DolbyEncodingEngine\dee.exe" ^
--dee-license "C:\Users\LumaVista\Documents\DolbyEncodingEngine\license.lic" ^
--ffmpeg "C:\Users\LumaVista\Documents\DolbyEncodingEngine\extensions_3rd-party\ffmpeg-7.1.1-full_build-shared\bin\ffmpeg.exe" ^
--input "D:\Cache Stock\DolbyVisionBluRayUHD\Mezzanine\DoVi_Mezz_ProRes.mov" ^
--metadata "D:\Cache Stock\DolbyVisionBluRayUHD\Mezzanine\DoVi_Meta_CMv4.0.xml" ^
--input-type mov_sidecar ^
--use-case no_mapping_with_mel ^
--optimize-mel-performance ^
--start 0 ^
--end 0 ^
--chunk 600 ^
--fps 59.94 ^
--gop-size 60 ^
--encode-pass-num 2 ^
--preset slower ^
--temp "X:\DolbyEncodingEngineTemp" ^
--progress-monitor ".\Progress.txt" ^
--base-layer "X:\DolbyVisionBluRayUHD\DEE_Workflow\DoViBL.hevc" ^
--enh-layer "X:\DolbyVisionBluRayUHD\DEE_Workflow\DoViEL.hevc"

pause
