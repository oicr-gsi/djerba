(example_demo_json)=

# Example JSON from demo plugins

```
$ cat report/djerba_report.json | python3 -m json.tool
{
    "core": {
        "author": "CGI Author",
        "document_config": "document_config.json",
        "report_id": "OICR-CGI-602c2791505e40ee847baf6b9fd65909",
        "extract_time": "2023-11-06_17:58:21Z"
    },
    "plugins": {
        "demo1": {
            "plugin_name": "demo1 plugin",
            "version": "1.0.0",
            "priorities": {
                "configure": 200,
                "extract": 200,
                "render": 200
            },
            "attributes": [
                "clinical"
            ],
            "merge_inputs": {
                "gene_information_merger": [
                    {
                        "Gene": "KRAS",
                        "Gene_URL": "https://www.oncokb.org/gene/KRAS",
                        "Chromosome": "12p12.1",
                        "Summary": "KRAS, a GTPase which functions as an upstream regulator of the MAPK and PI3K pathways, is frequently mutated in various cancer types including pancreatic, colorectal and lung cancers."
                    },
                    {
                        "Gene": "PIK3CA",
                        "Gene_URL": "https://www.oncokb.org/gene/PIK3CA",
                        "Chromosome": "3q26.32",
                        "Summary": "PIK3CA, the catalytic subunit of PI3-kinase, is frequently mutated in a diverse range of cancers including breast, endometrial and cervical cancers."
                    }
                ]
            },
            "results": {}
        },
        "demo2": {
            "plugin_name": "demo2 plugin",
            "version": "1.0.0",
            "priorities": {
                "configure": 300,
                "extract": 300,
                "render": 300
            },
            "attributes": [
                "clinical"
            ],
            "merge_inputs": {
                "gene_information_merger": [
                    {
                        "Gene": "PIK3CA",
                        "Gene_URL": "https://www.oncokb.org/gene/PIK3CA",
                        "Chromosome": "3q26.32",
                        "Summary": "PIK3CA, the catalytic subunit of PI3-kinase, is frequently mutated in a diverse range of cancers including breast, endometrial and cervical cancers."
                    },
                    {
                        "Gene": "PIK3CB",
                        "Gene_URL": "https://www.oncokb.org/gene/PIK3CB",
                        "Chromosome": "3q22.3",
                        "Summary": "PIK3CB, a catalytic subunit of PI3-kinase, is altered by amplification or mutation in various cancer types."
                    }
                ]
            },
            "results": {
                "answer": "Lorem ipsum",
                "question": "What do you get if you multiply six by nine?"
            }
        },
        "demo3": {
            "plugin_name": "demo3 plugin",
            "version": "1.0.0",
            "priorities": {
                "configure": 800,
                "extract": 800,
                "render": 800
            },
            "attributes": [
                "clinical"
            ],
            "merge_inputs": {},
            "results": {
                "salutation": "So long and thanks for all the fish!"
            }
        }
    },
    "mergers": {},
    "config": {
        "core": {
            "archive_name": "djerba",
            "archive_url": "http://${username}:${password}@${address}:${port}",
            "attributes": "",
            "author": "CGI Author",
            "configure_priority": "100",
            "depends_configure": "",
            "depends_extract": "",
            "document_config": "document_config.json",
            "extract_priority": "100",
            "render_priority": "100",
            "report_id": "OICR-CGI-602c2791505e40ee847baf6b9fd65909",
            "report_version": "1",
            "sample_info": "sample_info.json"
        },
        "demo1": {
            "question": "How many roads must we each walk down?",
            "attributes": "clinical",
            "configure_priority": "200",
            "depends_configure": "",
            "depends_extract": "",
            "dummy_file": "None",
            "extract_priority": "200",
            "render_priority": "200"
        },
        "demo2": {
            "demo2_param": "Lorem ipsum",
            "attributes": "clinical",
            "configure_priority": "300",
            "depends_configure": "",
            "depends_extract": "",
            "extract_priority": "300",
            "question": "question.txt",
            "render_priority": "300"
        },
        "demo3": {
            "salutation": "Greetings",
            "attributes": "clinical",
            "configure_priority": "800",
            "depends_configure": "",
            "depends_extract": "",
            "extract_priority": "800",
            "render_priority": "800"
        }
    }
}
```
