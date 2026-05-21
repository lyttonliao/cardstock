import {
  Combobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
} from "@/components/ui/combobox";

type SearchItem = {
  label: string,
  value: string | number | null,
  tags: string[],
}

export default function SearchForm({ items, onChange, onSelect }: { 
  items: SearchItem[],
  onChange: (val: string) => void,
  onSelect: (item: SearchItem) => void,
}) {
  return (
    <Combobox>
      <ComboboxInput placeholder="Search for a card.." onChange={(e) => onChange(e.target.value)} />
      <ComboboxContent>
        <ComboboxEmpty>No matches found.</ComboboxEmpty>
        <ComboboxList>
          {items.map((item) => (
            <ComboboxItem key={item.label} value={item.value} onClick={() => onSelect(item)}>
              <div className="grid grid-cols-3">
                <div>{item.label}</div>
                {item.tags.map((tag) => (
                  <div key={`${item.label}-${tag}`}>{tag}</div>
                ))}
              </div>
            </ComboboxItem>
          ))}
        </ComboboxList>
      </ComboboxContent>
    </Combobox>
  );
}