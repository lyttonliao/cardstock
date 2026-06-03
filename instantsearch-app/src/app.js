const { algoliasearch, instantsearch } = window;

const searchClient = algoliasearch(
  'S464CL5K33',
  'ca51ead66391971f232e051556434c52'
);

const search = instantsearch({
  indexName: 'cards_index',
  searchClient,
  future: { preserveSharedStateOnUnmount: true },
});

search.addWidgets([
  instantsearch.widgets.searchBox({
    container: '#searchbox',
  }),
  instantsearch.widgets.hits({
    container: '#hits',
    templates: {
      item: (hit, { html, components }) => html`
        <article>
          <img src=${hit.image_small} alt=${hit.name} />
          <div>
            <h1>${components.Highlight({ hit, attribute: 'name' })}</h1>
            <p>${components.Highlight({ hit, attribute: 'set_name' })}</p>
            <p>${components.Highlight({ hit, attribute: 'variant' })}</p>
            <p>${components.Highlight({ hit, attribute: 'rarity' })}</p>
          </div>
        </article>
      `,
    },
  }),
  instantsearch.widgets.configure({
    hitsPerPage: 8,
  }),
  instantsearch.widgets.pagination({
    container: '#pagination',
  }),
]);

search.start();
