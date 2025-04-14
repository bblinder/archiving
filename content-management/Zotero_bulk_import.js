// from this zotero.org thread:
// https://forums.zotero.org/discussion/78638/unable-to-bulk-import-a-list-of-urls/p1


// Methdodology/what the script does can be found here:
// https://www.zotero.org/support/dev/client_coding/javascript_api#running_ad_hoc_javascript_in_zotero


// In Zotero open Tools --> Developer --> 'Run Javascript'
// Paste this code, then Run.

var path = '/home/username/Desktop/urls.txt';
var urls = Zotero.File.getContents(path).split('\n').map(url => url);
await Zotero.HTTP.processDocuments(
	urls,
	async function (doc) {
		var translate = new Zotero.Translate.Web();
		translate.setDocument(doc);
		var translators = await translate.getTranslators();
		if (translators.length) {
			translate.setTranslator(translators[0]);
			try {
				await translate.translate();
				return;
			}
			catch (e) {}
		}
		await ZoteroPane.addItemFromDocument(doc);
	}
)