import platform, sys, os

# figure out the root directory
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
print('ROOT_DIR', ROOT_DIR)

# figure out what machine we're on, we only assume single node runs
MACHINE=None
uname = str(platform.uname().node)
if 'lassen' in uname:
    MACHINE = 'lassen'
    os.sched_setaffinity(0, {i for i in range(160)})
elif 'ruby' in uname:
    MACHINE = 'ruby'
    os.sched_setaffinity(0, {i for i in range(112)})
else:
    sys.exit('Unrecognized Machine Type from uname')

# specify the job launching approach for each machine
machines = {
    'ruby' : {
        'envvars': {
            'OMP_NUM_THREADS': [str(a) for a in [4,8,14,28,42,56,70,112]],
            'OMP_PROC_BIND': ['close', 'spread'],
            'OMP_SCHEDULE': ['static']+[ a+','+str(b) for a in ['static', 'guided', 'dynamic'] for b in [1,8,32,64,128,256,512] ],
        },
        'pythonToModLoad' : 'python/3.10.8',
        'jobsystem' : {
            'runner' : 'sbatch --nodes=1 ',
            'debug' : '--partition=pdebug ', 
            'nodetime' : '--time=', # in format of: minutes
            'output' : '--output=' # can do "path/to/file.log"
        }
    },

    'lassen' : {
        'envvars': {
            'OMP_NUM_THREADS': [str(a) for a in [10,20,40,60,80,100,120,140,160]],
            'OMP_PROC_BIND': ['close', 'spread'],
            'OMP_SCHEDULE': ['static']+[ a+','+str(b) for a in ['static', 'guided', 'dynamic'] for b in [1,8,32,64,128,256,512] ],
        },
        'pythonToModLoad' : 'python/3.8.2',
        'jobsystem' : {
            'runner' : 'bsub -nnodes 1 ',
            'debug' : '-qpdebug ', 
            'nodetime' : '-W ', # in format of: minutes
            'output' : '-o ' # can do "path/to/file.log"
        }
    }
}

# specify each program and how to gather/check it's output
progs = {
    'bt_nas': {
        'xtime-regex':r'(?<=Time in seconds =)(\s*\d*\.\d*)(?=\s)',
        'valid-regex':r'(Verification\s*=\s*SUCCESSFUL)(?=\s)',
        'dirname' : 'bt',
        'exe': {
            'smlprob': './bt.B.x',
            'medprob': './bt.C.x',
            'lrgprob': './bt.D.x'
        }
    },
    'cg_nas': {
        'xtime-regex':r'(?<=Time in seconds =)(\s*\d*\.\d*)(?=\s)',
        'valid-regex':r'(Verification\s*=\s*SUCCESSFUL)(?=\s)',
        'dirname' : 'cg',
        'exe': {
            'smlprob': './cg.B.x',
            'medprob': './cg.C.x',
            'lrgprob': './cg.D.x'
        }
    },
    'ft_nas': {
        'xtime-regex':r'(?<=Time in seconds =)(\s*\d*\.\d*)(?=\s)',
        'valid-regex':r'(Verification\s*=\s*SUCCESSFUL)(?=\s)',
        'dirname' : 'ft',
        'exe': {
            'smlprob': './ft.B.x',
            'medprob': './ft.C.x',
            'lrgprob': './ft.D.x'
        }
    },
#    'lu_nas': {
#        'xtime-regex':r'(?<=Time in seconds =)(\s*\d*\.\d*)(?=\s)',
#        'valid-regex':r'(Verification\s*=\s*SUCCESSFUL)(?=\s)',
#        'dirname' : 'lu',
#        'exe': {
#            'smlprob': './lu.B.x',
#            'medprob': './lu.C.x',
#            'lrgprob': './lu.D.x'
#        }
#    },
    'bfs_rodinia': {
        'xtime-regex':r'(?<=Compute time: )(\s*\d*\.\d*)(?=\s)',
        'valid-regex':'',
        'dirname' : 'bfs',
        'exe': {
            'smlprob': '"./bfs 1 ../inputs/graph4096.txt"',
            'medprob': '"./bfs 1 ../inputs/graph65536.txt"',
            'lrgprob': '"./bfs 1 ../inputs/graph1MW_6.txt"'
        }
    },
    'cfd_rodinia': {
        'xtime-regex':r'(?<=Compute time: )(\s*\d*\.\d*)(?=\s)',
        'valid-regex':'',
        'dirname' : 'cfd',
        'exe': {
            'smlprob': '"./euler3d_cpu ../inputs/fvcorr.domn.097K"',
            'medprob': '"./euler3d_cpu ../inputs/missile.domn.0.2M"',
            'lrgprob': '"./euler3d_cpu ../inputs/missile.domn.0.4M"'
        }
    },
    'hpcg': {
        'xtime-regex':r'(?<=Benchmark Time Summary::Total=)(\d*\.\d*)(?=\s)',
        'valid-regex':r'(?<=Final Summary::)(Results are valid)(?=\s)',
        'dirname' : 'hpcg',
        'exe': {
            'smlprob': '"rm -f *.txt" && "./xhpcg --nx=32 --ny=32 --nz=32" && "cat *.txt"',
            'medprob': '"rm -f *.txt" && "./xhpcg --nx=128 --ny=128 --nz=128" && "cat *.txt"',
            'lrgprob': '"rm -f *.txt" && "./xhpcg --nx=200 --ny=200 --nz=200" && "cat *.txt"'
        }
    },
    'lulesh': {
        'xtime-regex':r'(?<=\()\s*(\d*\.\d*)(?= overall\))',
        'valid-regex':'',
        'dirname' : 'lulesh',
        'exe':{
            'smlprob': '"./lulesh2.0 -s 30 -r 100 -b 0 -c 8 -i 200"',
            'medprob': '"./lulesh2.0 -s 55 -r 100 -b 0 -c 8 -i 200"',
            'lrgprob': '"./lulesh2.0 -s 80 -r 100 -b 0 -c 8 -i 200"',
        }
    },
}
