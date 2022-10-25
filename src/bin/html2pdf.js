'use strict';

const { triggerAsyncId } = require('async_hooks');

const puppeteer = require('puppeteer');

(async () => {

    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.goto(
      'report.html', {
        waitUntil: 'networkidle2',
    });
  
    await page.pdf(
      {path: 'report.pdf', 
      format: 'Letter',
      headerTemplate: '<h1></h1>',
      printBackground: true,
      footerTemplate: '<div style="font-family: Arial !important;font-size:10px!important;width: 15%;text-align:right; " class="pdfheader">Draft Report</div><div style="font-family: Arial !important;font-size:10px!important;width: 80%;text-align:right; " class="pdfheader"><span class="pageNumber"></span> of <span class="totalPages"></span></div>',
      displayHeaderFooter: true,
      margin: {
        top: "20px",
        bottom: "40px",
        left: "20px",
        right: "20px"
      }
      }
    );
  
    await browser.close();
    
})();