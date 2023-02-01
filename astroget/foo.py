hdu_corner_fields = ['CENRA1', 'CENDEC1',
                     'COR1RA1','COR1DEC1',
                     'COR2RA1','COR2DEC1',
                     'COR3RA1','COR3DEC1',
                     'COR4RA1','COR4DEC1' ]


# This spec contains examples of all features. Can only be used on rectype=Hdu
EXAMPLE1_outfields = [
            "md5sum",
            "archive_filename",
            "hdu:ra_center",
            "hdu:ra_min",
            "hdu:ra_max",
            "hdu:dec_min",
            "hdu:dec_max"
        ]
EXAMPLE1_constraints = {
    "hdu:ra_center": [ -400, 400], # Exclude HDUs with no ra/dec
    "caldat": ["2018-09-01", "2020-12-31"],
    "instrument": ["decam"],
    "proc_type": ["raw"],    # ["proc_type", "instcal"],
    "prod_type": ["image"],
    "obs_type": ["object"]}



found = client.find(outfields=['md5sum', 'archive_filename', 'url', 'filesize',
                               'ra_center', 'dec_center',
                               'instrument', 'proc_type', 'obs_type',
                               'release_date', 'caldat'],
                    constraints={'instrument': ['decam'],
                                 'obs_type': ['object'],
                                 'proc_type': ['instcal']}
                    )


#
{
  "outfields": [
    "md5sum",
    "ra_min",
    "archive_filename",
    "instrument",
    "proc_type",
    "obs_type",
    "release_date",
    "proposal",
    "caldat"
  ],
  "search": [
    [
      "telescope",
      "ct4m"
    ],
    [
      "instrument",
      "decam"
    ],
    [
      "obs_type",
      "object"
    ],
    [
        "proc_type",o
      "instcal"
    ]
  ]
}

# See: ~/sandbox/notes/noirlab/cutouts.org:*Retrieve data
found = client.find(outfields=['url', 'filesize', "archive_filename",
                               'ra_center', 'dec_center',
                               'instrument', 'proc_type', 'obs_type'],
                    constraints={'instrument': ['decam'],
                                 'ra_center': [ra - radius, ra + radius],
                                 'dec_center': [dec - radius, dec + radius],
                                 'obs_type': ['object'],
                                 'proc_type': ['instcal']},
                    sort="filesize"
                    )
{r['url']: f"{r['filesize']:,}" for r in found.records}

{'https://astroarchive.noirlab.edu/api/retrieve/a099661b099dc299aff828a753367ee8/': '4,351,680',
 'https://astroarchive.noirlab.edu/api/retrieve/d0265c8410237b5dfc78c0159abfa065/': '5,037,120',
 'https://astroarchive.noirlab.edu/api/retrieve/21c1c25b43f6b91b85ffd8b2fff87f11/': '5,451,840',
 'https://astroarchive.noirlab.edu/api/retrieve/cf05b7cdb739fb8277028ec28e1f65fa/': '6,658,560',
 'https://astroarchive.noirlab.edu/api/retrieve/60ba93e0e704329b6c708698fb7e479e/': '7,211,520',
 'https://astroarchive.noirlab.edu/api/retrieve/c1e58fae7a33e0a48e6fc268b69e672e/': '7,819,200',
 'https://astroarchive.noirlab.edu/api/retrieve/98a5fbecc45a72f65dc29e2749ad041c/': '262,572,480',
 'https://astroarchive.noirlab.edu/api/retrieve/a508a8455a83bc460022c00b23d9bb46/': '263,125,440',
 'https://astroarchive.noirlab.edu/api/retrieve/884fb3ded4bb6fafa60ae002a937dd22/': '268,119,360',
 'https://astroarchive.noirlab.edu/api/retrieve/9d0eaf875390ff3fc73e1d382aa992f8/': '319,328,640',
 'https://astroarchive.noirlab.edu/api/retrieve/fadba9ce76fef60ddc49b2d2cae85141/': '319,743,360',
 'https://astroarchive.noirlab.edu/api/retrieve/e6c2c72ce0ce318f527bf1ec75a0ed40/': '320,083,200',
 'https://astroarchive.noirlab.edu/api/retrieve/b6566bc67e68d6ab7d55075b539f2b1b/': '320,480,640',
 'https://astroarchive.noirlab.edu/api/retrieve/c176223f5a49ee2020ae6f089760a270/': '321,071,040',
 'https://astroarchive.noirlab.edu/api/retrieve/6245c9ec8805b147010646a69e093bd8/': '321,462,720',
 'https://astroarchive.noirlab.edu/api/retrieve/2ab885d0b1c175d57de00588679d6a1f/': '321,546,240',
 'https://astroarchive.noirlab.edu/api/retrieve/a7baaa9d442d916113e7a9c2a3faacda/': '323,732,160',
 'https://astroarchive.noirlab.edu/api/retrieve/b1dbbe234ae87da3b031ff621699643b/': '326,658,240'}

4.2mb c4d_180315_064354_ood_r_ls9.fits.fz a099661b099dc299aff828a753367ee8
...
312mb c4d_170317_075741_oow_z_v1.fits.fz  b1dbbe234ae87da3b031ff621699643b  <<<

1.7gb c4d_180208_004814_ooi_z_ls9.fits.fz 1431f0096dd79c70ea1d5ac78282d508

https://noirlab.edu/science/programs/ctio/instruments/Dark-Energy-Camera/characteristics
<
