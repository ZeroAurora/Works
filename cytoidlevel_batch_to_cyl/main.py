# SPDX-License-Identifier: GLWTPL

from pathlib import Path
import json
from zipfile import ZipFile


DEFAULT_CHART_INFO = {
    "DiffName": "Charter",
    "Media": "ECHIDNA.ogg",
    "Bg": "Background4-3.png",
    "Icon": "",
    "SongName": "",
    "ThemeColor": "#FF84B6BF",
    "DiffTextColor": "#B3FF33FF",
    "DiffBgColor": "#FF330033"
}

in_path = Path("./in")
out_path = Path("./out")
levels = list(in_path.glob("*.cytoidlevel"))

cyl = {
    "Version": 0,
    "ChartInfos": [],
}

with ZipFile(levels[0]) as std_level:
    std_level.extract(DEFAULT_CHART_INFO["Media"], out_path)
    std_level.extract(DEFAULT_CHART_INFO["Bg"], out_path)
    print("Procceed media files.")

for level in levels:
    with ZipFile(level) as zip:
        with zip.open("level.json") as level_spec:
            chart_path = json.load(level_spec)["charts"][0]["path"] # type: str
        chart_id = str(chart_path.split(".")[0])
        zip.extract(chart_path, out_path)
        cyl["ChartInfos"].append(
            DEFAULT_CHART_INFO | {"FileName": chart_path, "Diff": chart_id}
        )
        print("Procceed {}.".format(chart_path))

with open(out_path / "CylheimProject.cyl", "w") as cyl_file:
    json.dump(cyl, cyl_file)
    print("Finished Processing.")