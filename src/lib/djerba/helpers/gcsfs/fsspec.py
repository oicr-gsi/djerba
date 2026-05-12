import subprocess
import gcsfs

fs = gcsfs.GCSFileSystem()

with fs.open("gs://my-bucket/file.csv", "rb") as f:
    subprocess.run(
        ["Rscript", "script.R"],
        stdin=f,
        check=True
    )

#path = fs.get("gs://bucket/file.csv", "/tmp/file.csv")
#subprocess.run(["Rscript", "script.R", "/tmp/file.csv"])
#--> manage cleanup