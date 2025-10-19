import { Select, Tag } from "antd";

export default function RunPicker({ runs, value, onChange }) {
  const options = runs.map((r) => ({
    label: (
      <div className="run-option">
        <span className="run-name" title={r.name}>{r.name}</span>
        <span className="run-tags">
          {r.model ? <Tag color="blue" style={{ marginInline: 0 }}>{r.model}</Tag> : null}
          {r.experiment ? <Tag color="geekblue" style={{ marginInline: 0 }}>{r.experiment}</Tag> : null}
        </span>
      </div>
    ),
    value: r.name,
  }));
  return (
    <Select
      showSearch
      style={{ width: "100%" }}
      placeholder="Pick a run"
      optionFilterProp="label"
      popupMatchSelectWidth={false}
      dropdownStyle={{ width: 'clamp(520px, 55vw, 1100px)', maxWidth: '90vw' }}
      value={value}
      options={options}
      onChange={onChange}
    />
  );
}
