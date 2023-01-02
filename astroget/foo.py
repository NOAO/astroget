found = client.find(outfields=['md5sum', 'archive_filename', 'url', 'filesize',
                               'ra_center', 'dec_center',
                               'instrument', 'proc_type', 'obs_type',
                               'release_date', 'caldat'],
                    constraints={'instrument': ['decam'],
                                 'obs_type': ['object'],
                                 'proc_type': ['instcal']}
                    )
