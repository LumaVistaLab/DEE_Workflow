"""
 BSD 3-Clause License

 Copyright (c) 2019, Dolby Laboratories
 All rights reserved.

 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions are met:

 * Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

 * Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

 * Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
# !/usr/bin/env python
import time
import datetime
import argparse
import sys
import os
import subprocess

# Stores global config and data provided by parser
class Config:
    def __init__(self):
        self.validate_parsing()
        self.script_dir = os.path.dirname(__file__)
        self.templates = {"bl_yuv_mxf" : os.path.join(self.script_dir, '../dv_mezz_to_dv_profile_7_bl/mxf_sidecar_index_dv_mezz_to_dv_profile_7_bl_yuv420p10le_manifest.xml'),
                        "bl_yuv_mxf_sidecar" : os.path.join(self.script_dir, '../dv_mezz_to_dv_profile_7_bl/mxf_sidecar_index_dv_mezz_to_dv_profile_7_bl_yuv420p10le_manifest.xml'),
                        "bl_yuv_mov_sidecar" : os.path.join(self.script_dir, '../dv_mezz_to_dv_profile_7_bl/mov_sidecar_dv_mezz_to_dv_profile_7_bl_yuv420p10le_manifest.xml'),
                        "encode_yuv_hevcbl" : os.path.join(self.script_dir, '../encode_to_hevc/bl/x265/yuv420_encode_to_hevc_hevc.xml'),
                        "encode_yuv_hevcel" : os.path.join(self.script_dir, '../encode_to_hevc/el/x265/yuv420_encode_to_hevc_hevc.xml'),
                        "encode_yuv_beamrbl" : os.path.join(self.script_dir, '../encode_to_hevc/bl/beamr/yuv420_encode_to_hevc_hevc.xml'),
                        "encode_yuv_beamrel" : os.path.join(self.script_dir, '../encode_to_hevc/el/beamr/yuv420_encode_to_hevc_hevc.xml'),
                        "encode_yuv_impactbl" : os.path.join(self.script_dir, '../encode_to_hevc/bl/impact/yuv420_encode_to_hevc_hevc.xml'),
                        "encode_yuv_impactel" : os.path.join(self.script_dir, '../encode_to_hevc/el/impact/yuv420_encode_to_hevc_hevc.xml'),
                        "el_yuv_mxf" : os.path.join(self.script_dir, '../dv_mezz_to_dv_profile_7_el/mxf_sidecar_index_yuv420_manifest_dv_mezz_to_dv_profile_7_el_yuv420_rpu_manifest.xml'),
                        "el_yuv_mxf_sidecar" : os.path.join(self.script_dir, '../dv_mezz_to_dv_profile_7_el/mxf_sidecar_index_yuv420_manifest_dv_mezz_to_dv_profile_7_el_yuv420_rpu_manifest.xml'),
                        "el_yuv_mov_sidecar" : os.path.join(self.script_dir, '../dv_mezz_to_dv_profile_7_el/mov_sidecar_yuv420_manifest_dv_mezz_to_dv_profile_7_el_yuv420_rpu_manifest.xml'),
                        "vesmux": os.path.join(self.script_dir, '../dv_ves_mux/bl_el_rpu_dv_ves_mux_hevc.xml'),
                        "md_postproc" : os.path.join(self.script_dir, '../dv_md_postproc/hevc_dv_md_postproc_hevc.xml'),
                        "parse_mxf" : os.path.join(self.script_dir, '../parse_mxf/mxf_parse_mxf_index_dvmd.xml')}
        self.layer_params = {'bl' : self.get_data_rate('bl'),
                             'el' : self.get_data_rate('el')}
        self.max_scene_frames = min(max(self.gop_size * 2, 12), 256)
        self.preset = self.get_encoder_preset()
        self.chunks = self.get_chunks()

    def get_data_rate(self, layer):
        #Returns [data_rate, max_vbv_data_rate, vbv_buffer_size] (in kbps) for specified layer.
        if 'mel' in self.use_case:
            if layer is 'bl':
                return [85000, 85000, 93500]
            else:
                return [500, 500, 550]
        else:
            if layer is 'bl':
                return [85000, 85000, 93500]
            else:
                return [15000, 15000, 16500]
        
    def get_available_encoder_presets(self):
        if self.encoder == 'hevc':
            encoder_preset = ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow', 'placebo']
        elif self.encoder == 'beamr':
            encoder_preset = ['insanely_slow', 'ultra_slow', 'very_slow', 'slower', 'slow', 'medium', 'medium_plus', 'fast', 'faster', 'ultra_fast', 'insanely_fast']
        elif self.encoder == 'impact':
            encoder_preset = ['0', '10', '11', '20', '21', '32', '33', '40', '41', '50', '51', '52', '53']
        return encoder_preset

    def get_encoder_preset(self):
        if self.preset:
            return self.preset
        else:
            return self.get_default_encoder_preset()
    
    def get_default_encoder_preset(self):
        if self.encoder == 'beamr':
            return 'slow'
        elif self.encoder == 'hevc':
            return 'slower'
        elif self.encoder == 'impact':
            return '10'
    
    def get_chunks(self):
        chunks = [Chunk(start, start + self.chunk - 1) for start in range(self.start, self.end+1, self.chunk)]
        chunks[-1].end = self.end                           #fix possible overflow

        if chunks[-1].num_of_frames() < 2 * self.gop_size:  # if the last chunk is too small, add it to the previous chunk
            chunks.pop()
            chunks[-1].end = self.end

        chunks[0].concatenate = 'false'
        return chunks
    
    def validate_parsing(self):
        if self.input_type in ['mxf_sidecar', 'mov_sidecar'] and not self.metadata:
            print('ERROR: Input of type {} requires metadata file.'.format(self.input_type))
            sys.exit(1)
        
        if not os.path.isdir(self.temp):
            print('ERROR: Provided temp directory is invalid: {}'.format(self.temp))
            sys.exit(1)
        
        if self.chunk < 2 * self.gop_size:
            print('ERROR: Chunk size too small.')
            sys.exit(1)

        if self.end - self.start + 1 < 2 * self.gop_size:
            print('Selected content length is too short for the current gop size.')
            sys.exit(1)

        if self.preset and self.preset not in self.get_available_encoder_presets():
            print('ERROR: Preset option invalid (selected encoder: {}, selected preset: {}).'.format(self.encoder, self.preset))
            sys.exit(1)

class FileManager:
    def __init__(self):
        self.time_stamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')
        self.tracked_files = []
    
    def get_name(self, unique_identifier, directory = None):
        global config
        if directory is None:
            directory = config.temp
        file_path = os.path.abspath(os.path.join(directory, self.time_stamp + unique_identifier))
        return file_path

    def track_file(self, unique_identifier, directory = None):
        global config
        if directory is None:
            directory = config.temp
        file_path = self.get_name(unique_identifier, directory)
        self.tracked_files.append(file_path)
        return file_path

    def clean_temp(self):
        global config
        if not config.keep_temp:
            for file in self.tracked_files:
                if os.path.exists(file) and os.path.isfile(file):
                    os.remove(file)

class Chunk:
    def __init__(self, start, end, concatenate = 'true'):
        self.start = start
        self.end = end
        self.concatenate = concatenate

    def num_of_frames(self):
        return self.end - self.start + 1

# Calls wrapped object and prints it's output
class Print:
    def __init__(self, wrapped):
        self.wrapped = wrapped
    def __call__(self):
        out = self.wrapped()
        self._run(out)
        return out
    def _run(self, out):
            print('CMD: {} \n'.format(' '.join(out)))

# Calls wrapped object and runs it's outputs as subprocesses
class RunCmd:
    def __init__(self, wrapped):
        self.wrapped = wrapped
    def __call__(self):
        out = self.wrapped()
        self._run(out)

    def _run(self, cmd):
        global config
        try:
            self.run_subprocess(cmd, config.print_all)
        except OSError as e:
            print('ERROR: Command execution failed: {}'.format(e))
            sys.exit(1)
        
    def run_subprocess(self, cmd, print_all):
        if print_all:
            rc = subprocess.call(cmd)
        else:
            rc = subprocess.call(cmd, stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'))

        if rc:
            print('ERROR: Command execution failed: {}'.format(rc))
            sys.exit(2)

# Creates and handles workflow based on global config
class Workflow:
    def __init__(self):
        self.steps = []
    def set_steps(self):
        global config
        if config.dry_run:
            self.steps = self.get_run_dry_steps()
        else:
            self.steps = self.get_normal_run_steps()

    def get_run_dry_steps(self):
        global config
        run_dry_steps = [Print(sanity_check_dee), 
                         Print(sanity_check_ffmpeg)]

        if config.input_type in ['mxf', 'mxf_sidecar']:
            run_dry_steps.append(Print(parse_mxf))

        for chunk in config.chunks:
            run_dry_steps.extend([Print(Generate_bl_yuv(chunk)),
                                  Print(Encode_yuv(chunk, 'bl')),
                                  Print(Decode_bl_hevc(chunk)),
                                  Print(Generate_el_yuv(chunk)),
                                  Print(Encode_yuv(chunk, 'el')),
                                  Print(Vesmux(chunk))
            ])
        run_dry_steps.append(Print(md_postproc))

        if config.dvesverifier:
            run_dry_steps.insert(0, Print(sanity_check_dvesverifier))
            run_dry_steps.append(Print(verify))

        return run_dry_steps
    
    def get_normal_run_steps(self): 
        normal_run_steps = [RunCmd(step) for step in self.get_run_dry_steps()]
        if config.dvesverifier: #add concatenation before postprocessing
            normal_run_steps.insert(-2, Concatenate_chunk_files('bl'))
            normal_run_steps.insert(-2, Concatenate_chunk_files('el'))
        else:
            normal_run_steps.insert(-1, Concatenate_chunk_files('bl'))
            normal_run_steps.insert(-1, Concatenate_chunk_files('el'))

        return normal_run_steps

    def run(self):
        for step in self.steps:
            step()

def create_parser():
    class toAbsolutePath(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, os.path.abspath(values))

    parser = argparse.ArgumentParser(
        description='Dolby Vision profile 7 distributed encoding workflow.', add_help=False)
    parser._positionals.add_argument('-u', '--use-case', help='Use-case. Values: no_mapping_with_mel|no_mapping_with_fel|map_to_1000_nits_with_fel|map_to_1000_nits_with_mel|map_to_600_nits_with_fel.', choices=['no_mapping_with_mel', 'no_mapping_with_fel', 'map_to_1000_nits_with_fel', 'map_to_1000_nits_with_mel', 'map_to_600_nits_with_fel'], required=True)
    parser._positionals.add_argument('-t', '--input-type', help='Input type. Values: mxf|mxf_sidecar|mov_sidecar.', choices=['mxf', 'mxf_sidecar', 'mov_sidecar'], required=True)
    parser._positionals.add_argument('-l', '--dee-license', help='DEE license file.',action=toAbsolutePath, required=True, metavar='FILE')
    parser._positionals.add_argument('-i', '--input', help='Input mezzanine file.',action=toAbsolutePath, required=True, metavar='FILE')
    parser._positionals.add_argument('-g', '--gop-size', help='GOP size in number of frames.', type=int, required=True, metavar='NUM')
    parser._positionals.add_argument('-e', '--enh-layer', help='Output EL stream.',action=toAbsolutePath, required=True, metavar='FILE')
    parser._positionals.add_argument('-d', '--dee', help='DEE application.', required=True, metavar='FILE')
    parser._positionals.add_argument('-c', '--chunk', help='Chunk size in number of frames.', type=int, required=True, metavar='NUM')
    parser._positionals.add_argument('-b', '--base-layer', help='Output BL stream.',action=toAbsolutePath, required=True, metavar='FILE')
    parser._positionals.add_argument('--temp', help='Temp directory.',action=toAbsolutePath, required=True, metavar='DIR')
    parser._positionals.add_argument('--start', help='Start frame.', type=int, required=True, metavar='NUM')
    parser._positionals.add_argument('--fps', help='Video frame-rate. Values: 23.976|24|25|50|59.94|60.', choices=['23.976', '24', '25', '50', '59.94', '60'], required=True, metavar='NUM')
    parser._positionals.add_argument('--end', help='End frame.', type=int, required=True, metavar='NUM')

    parser._optionals.add_argument('-p', '--encode-pass-num', help='Number of encoder passes to run for each layer.', type=int, default=2, required=False, metavar='NUM')
    parser._optionals.add_argument('-m', '--metadata', help='Input metadata file. Used only by input types with sidecar metadata.',action=toAbsolutePath, required=False, metavar= 'FILE')
    parser._optionals.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help='Print this help and exit.')
    parser._optionals.add_argument('--print-all', help='Print all logs to stdout.', required=False, action='store_true')
    parser._optionals.add_argument('--preset', help='Encoder preset/speed mode. If not specified, a default will be used.', required=False, metavar='TYPE')
    parser._optionals.add_argument('--keep-temp', help='Keep outputs of intermediate steps.', required=False, action='store_true')
    parser._optionals.add_argument('--ffmpeg', help='Ffmpeg application.', required=False, default='ffmpeg', metavar='FILE')
    parser._optionals.add_argument('--encoder', help='Encoder type. Values: hevc|impact|beamr.', choices=['hevc', 'impact', 'beamr'], required=False, default='hevc', metavar='TYPE')
    parser._optionals.add_argument('--dvesverifier', help='Dolby Vision ES Verifier application.', required=False, metavar='FILE')
    parser._optionals.add_argument('--dry-run', help='Print commands, but do not run them.', required=False, action='store_true')

    parser._positionals.title = 'Required'
    parser._optionals.title = 'Optional'
    return parser

def parse_mxf():
    global config, file_manager

    mezz_input = config.input
    cmd = [config.dee
        ,'-l', config.dee_license
        ,'-x', config.templates['parse_mxf']
        ,'--input-video', mezz_input
        ,'--add-elem','misc:temp_dir:path=' + config.temp
    ]

    if config.input_type == 'mxf':
        cmd.extend(['--output', file_manager.track_file('.json', os.path.dirname(config.input)) +
                          ',' + file_manager.track_file('.xml', os.path.dirname(config.input))])
    else:
        cmd.extend(['--add-elem','filter:extract_dv_md=false'
                    ,'--output', file_manager.track_file('.json', os.path.dirname(config.input))])
    
    return cmd

class Generate_bl_yuv:
    def __init__(self, chunk):
        self.chunk = chunk
    def __call__(self):
        global config, file_manager

        mezz_input = config.input
        if config.input_type == 'mxf':
            mezz_input += ',' + file_manager.get_name('.xml', os.path.dirname(config.input))
        elif config.input_type in ['mxf_sidecar', 'mov_sidecar']:
            mezz_input += ',' + config.metadata

        cmd = [config.dee
            ,'-l', config.dee_license
            ,'-x', config.templates['bl_yuv_'+config.input_type]
            ,'--input-video', mezz_input
            ,'--output', file_manager.track_file('_' + str(self.chunk.start) +'_' + str(self.chunk.end) + '_' + 'bl.yuv')
            ,'--output', file_manager.track_file('_' + str(self.chunk.start) +'_' + str(self.chunk.end) + '_' + 'bl_manifest.xml')
            ,'--add-elem','filter:video:use_case=' + str(config.use_case)
            ,'--add-elem','filter:video:start=' + str(self.chunk.start)
            ,'--add-elem','filter:video:end=' + str(self.chunk.end)
            ,'--add-elem','misc:temp_dir:path=' + str(config.temp)
        ]
        if config.input_type in ['mxf', 'mxf_sidecar']:
            cmd.extend(['--add-elem','input:video:index_file_name=' +str(os.path.basename(file_manager.get_name('.json')))])

        return cmd

class Encode_yuv:
    def __init__(self, chunk, layer):
        self.chunk = chunk
        self.layer = layer
    def __call__(self):
        global config, file_manager

        cmd = [config.dee
            ,'-l', config.dee_license
            ,'-x', config.templates['encode_yuv_'+config.encoder+self.layer]
            ,'--input-video', file_manager.get_name('_' + str(self.chunk.start) +'_' + str(self.chunk.end) + '_' + self.layer + '.yuv')
            ,'--input-video', file_manager.get_name('_' + str(self.chunk.start) +'_' + str(self.chunk.end) + '_' + self.layer + '_manifest.xml')
            ,'--output', file_manager.track_file('_' + str(self.chunk.start) +'_' + str(self.chunk.end) + '_' + self.layer + '.hevc')
            ,'--add-elem','input:video:frame_rate=' + str(config.fps)
            ,'--add-elem','filter:video:data_rate=' + str(config.layer_params[self.layer][0])
            ,'--add-elem','filter:video:max_vbv_data_rate=' + str(config.layer_params[self.layer][1])
            ,'--add-elem','filter:video:vbv_buffer_size=' + str(config.layer_params[self.layer][2])
            ,'--add-elem','filter:video:encode_pass_num=' + str(config.encode_pass_num)
            ,'--add-elem','filter:video:concatenation_flag=' + self.chunk.concatenate
            ,'--add-elem','misc:temp_dir:path=' + config.temp
        ]
        if config.encoder == 'beamr':
            cmd.extend(['--add-elem', 'filter:video:gop_intra_period=' + str(config.gop_size),
                        '--add-elem', 'filter:video:gop_min_intra_period=' +str(config.gop_size),
                        '--add-elem','filter:video:encode_to_hevc:hevc_enc:param=' +'rc.look_ahead='+ str(config.gop_size)])
        else:
            cmd.extend(['--add-elem', 'filter:video:max_intra_period=' + str(config.gop_size),
                        '--add-elem', 'filter:video:min_intra_period=' +str(config.gop_size),
                        '--add-elem','filter:video:lookahead_frames=' + str(config.gop_size)])

        if config.encoder == 'impact':
            cmd.extend(['--add-elem', 'filter:video:encode_to_hevc:hevc_enc:speed_mode='+config.preset])
        else:
            cmd.extend(['--add-elem', 'filter:video:encode_to_hevc:hevc_enc:preset='+config.preset])
            
        return cmd


class Decode_bl_hevc:
    def __init__(self, chunk):
        self.chunk = chunk
    def __call__(self):
        global config, file_manager
        """
        This step is implemented using ffmpeg, just as an example.
        There are no special requirements for HEVC decoder, so implementation
        can be replaced with the other decoder/tool.
        Decoding BL HEVC can be also performed within EL YUV generation step,
        but hevc_dec plugin is required for that.
        """
        return [config.ffmpeg
            ,'-f', 'hevc', '-vsync', '0'
            ,'-i', file_manager.get_name('_' + str(self.chunk.start) +'_' + str(self.chunk.end) + '_' + 'bl.hevc')
            ,'-f', 'rawvideo'
            ,'-pix_fmt', 'yuv420p10le'
            ,file_manager.track_file('_' + str(self.chunk.start) +'_' + str(self.chunk.end) + '_' + 'bl_decoded.yuv')
        ]


class Generate_el_yuv:
    def __init__(self, chunk):
        self.chunk = chunk
    def __call__(self):
        global config, file_manager

        mezz_input = config.input

        if config.input_type == 'mxf':
            mezz_input += ',' + file_manager.get_name('.xml', os.path.dirname(config.input))
        elif config.input_type in ['mxf_sidecar', 'mov_sidecar']:
            mezz_input += ',' + config.metadata

        cmd = [config.dee
                ,'-l', config.dee_license
                ,'-x', config.templates['el_yuv_'+config.input_type]
                ,'--input-video', mezz_input
                ,'--input-video', file_manager.get_name('_'+ str(self.chunk.start) + '_' + str(self.chunk.end) + '_' + 'bl_decoded.yuv')
                ,'--input-video', file_manager.get_name('_' + str(self.chunk.start) + '_' + str(self.chunk.end) + '_' + 'bl_manifest.xml')
                ,'--output', file_manager.track_file('_' + str(self.chunk.start) + '_' + str(self.chunk.end) + '_' + 'el.yuv')
                     + ',' + file_manager.track_file('_' + str(self.chunk.start) + '_' + str(self.chunk.end) + '_' + 'el.rpu')
                ,'--output', file_manager.track_file('_' + str(self.chunk.start) + '_' + str(self.chunk.end) + '_' + 'el_manifest.xml')
                ,'--add-elem','filter:video:max_scene_frames=' + str(config.max_scene_frames)
                ,'--add-elem','misc:temp_dir:path=' + config.temp
        ]
        if config.input_type in ['mxf', 'mxf_sidecar']:
            cmd.extend(['--add-elem','input:video:index_file_name=' +str(os.path.basename(file_manager.get_name('.json')))])

        return cmd
class Vesmux:
    def __init__(self, chunk):
        self.chunk = chunk
    def __call__(self):
        global config, file_manager

        return [config.dee
                ,'-l', config.dee_license
                ,'-x', config.templates['vesmux']
                ,'--input-video', file_manager.get_name('_'+str(self.chunk.start)+'_'+str(self.chunk.end)+'_'+'el.rpu')
                          + ',' + file_manager.get_name('_'+str(self.chunk.start)+'_'+str(self.chunk.end)+'_'+'el.hevc')
                ,'--output',      file_manager.track_file('_'+str(self.chunk.start)+'_'+str(self.chunk.end)+'_'+'el_muxed.hevc')
                ,'--add-elem','misc:temp_dir:path=' + config.temp
        ]

class Concatenate_chunk_files:
    def __init__(self, layer):
        self.layer = layer
    def __call__(self):
        global config, file_manager

        if self.layer == 'el':
            name = lambda chunk : '_' + str(chunk.start) + '_' + str(chunk.end) + '_' + self.layer + '_muxed.hevc'
        else:
            name = lambda chunk : '_' + str(chunk.start) + '_' + str(chunk.end) + '_' + self.layer + '.hevc'

        filenames = [file_manager.get_name(name(chunk)) for chunk in config.chunks]

        with open(file_manager.track_file('_' + self.layer + '_concat.hevc'), 'ab') as out_file:
            for fname in filenames:
                with open(fname, 'rb') as file:
                    out_file.write(file.read())

def md_postproc():
    global config, file_manager

    return [config.dee
            ,'-l', config.dee_license
            ,'-x', config.templates['md_postproc']
            ,'--input-video', file_manager.get_name('_el_concat.hevc')
            ,'--input-video', file_manager.get_name('_bl_concat.hevc')
            ,'--output', config.enh_layer
            ,'--output', config.base_layer
            ,'--add-elem','input:video:hevc[0]:frame_rate=' + str(config.fps)
            ,'--add-elem','input:video:hevc[1]:frame_rate=' + str(config.fps)
            ,'--add-elem','misc:temp_dir:path=' + config.temp
    ]

def verify():
    global config

    return [config.dvesverifier 
            ,'-i', config.base_layer
            ,'-el', config.enh_layer
            ,'-dp', '7'
        ]

def sanity_check_dee():
    global config

    return [config.dee]

def sanity_check_dvesverifier():
    global config

    return [config.dvesverifier]

def sanity_check_ffmpeg():
    global config
    
    return [config.ffmpeg, '-version']

if __name__ == '__main__': 
    parser = create_parser()
    parser.parse_args(namespace=Config)

    config = Config()               #global
    file_manager = FileManager()    #global

    workflow = Workflow()
    workflow.set_steps()
    workflow.run()

    file_manager.clean_temp()
