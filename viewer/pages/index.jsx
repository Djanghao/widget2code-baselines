import { useEffect, useMemo, useState } from "react";
import { Layout, Typography, Input, Empty, Spin, Flex, Divider, Modal, Button, message } from "antd";
import { MenuFoldOutlined, MenuUnfoldOutlined, EyeOutlined, ExperimentOutlined, DownloadOutlined, CheckCircleOutlined } from "@ant-design/icons";
import Link from "next/link";
import { useRouter } from "next/router";
import RunPicker from "../components/RunPicker";
import PreviewCard from "../components/PreviewCard";
import CheckRunModal from "../components/CheckRunModal";

const { Sider } = Layout;
const { Title, Text } = Typography;

export default function Home() {
  const router = useRouter();
  const [runs, setRuns] = useState([]);
  const [run, setRun] = useState(null);
  const [images, setImages] = useState([]);
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState(null);
  const [loadingImages, setLoadingImages] = useState(false);
  const [loadingResults, setLoadingResults] = useState(false);
  const [results, setResults] = useState({});
  const [sourceModalOpen, setSourceModalOpen] = useState(false);
  const [siderCollapsed, setSiderCollapsed] = useState(false);
  const [renderStatus, setRenderStatus] = useState('idle');
  const [checkModalOpen, setCheckModalOpen] = useState(false);
  const [checkData, setCheckData] = useState(null);
  const [checkLoading, setCheckLoading] = useState(false);
  const [checkError, setCheckError] = useState(null);
  const [isMobile, setIsMobile] = useState(false);

  // Detect screen size and auto-collapse sidebar on mobile
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile && !siderCollapsed) {
        setSiderCollapsed(true);
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    fetch("/api/runs").then((r) => r.json()).then((d) => {
      setRuns(d.runs || []);
      const runFromUrl = router.query.run;
      if (runFromUrl && d.runs && d.runs.some(r => r.name === runFromUrl)) {
        setRun(runFromUrl);
      } else if (d.runs && d.runs.length > 0) {
        setRun(d.runs[0].name);
      }
    });
  }, [router.query.run]);

  useEffect(() => {
    if (!run) return;
    setLoadingImages(true);
    fetch(`/api/images?run=${encodeURIComponent(run)}`)
      .then((r) => r.json())
      .then((d) => {
        const list = (d.images || []).sort((a, b) => (a.id > b.id ? 1 : -1));
        setImages(list);
        setSelected(list.length ? list[0].id : null);
      })
      .finally(() => setLoadingImages(false));
  }, [run]);

  useEffect(() => {
    if (!run || !selected) return;
    setLoadingResults(true);
    fetch(`/api/results?run=${encodeURIComponent(run)}&image=${encodeURIComponent(selected)}`)
      .then((r) => r.json())
      .then((d) => setResults(d.categories || {}))
      .finally(() => setLoadingResults(false));

    const triggerBackgroundRender = async () => {
      try {
        const checkRes = await fetch(`/api/check-pngs?run=${encodeURIComponent(run)}&image=${encodeURIComponent(selected)}`);
        const check = await checkRes.json();
        if (check && check.complete) {
          console.log(`[viewer] PNG completeness: complete (total=${check.total})`);
          setRenderStatus('ready');
        } else {
          console.log(`[viewer] PNG completeness: incomplete (missing=${check?.missingCount ?? 'unknown'}). Starting background render...`);
          setRenderStatus('rendering');
          fetch('/api/batch-render', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ run, image: selected })
          }).catch(err => console.error('Background render failed:', err));
        }
      } catch (err) {
        console.error('PNG check failed:', err);
        setRenderStatus('ready');
      }
    };
    triggerBackgroundRender();
  }, [run, selected]);

  const filtered = useMemo(() => {
    if (!filter) return images;
    const f = filter.toLowerCase();
    return images.filter((i) => i.id.toLowerCase().includes(f));
  }, [images, filter]);

  const selectedItem = useMemo(() => images.find((i) => i.id === selected), [images, selected]);
  const selectedSource = useMemo(() => {
    if (!run || !selectedItem || !selectedItem.source) return null;
    return `/api/file?run=${encodeURIComponent(run)}&file=${encodeURIComponent(selectedItem.source)}`;
  }, [run, selectedItem]);

  const handleDownloadAll = async () => {
    if (!run) {
      message.warning('No run selected');
      return;
    }

    try {
      const url = `/api/download-all?run=${encodeURIComponent(run)}`;

      const response = await fetch(url);

      if (!response.ok) {
        const data = await response.json();
        if (data.message) {
          message.error(data.message);
        } else {
          message.error(data.error || 'Download failed');
        }
        return;
      }

      window.location.href = url;
      message.success('Preparing download...');
    } catch (err) {
      console.error('Download all failed:', err);
      message.error('Failed to download');
    }
  };

  const handleCheckRun = async () => {
    if (!run) {
      message.warning('No run selected');
      return;
    }
    setCheckModalOpen(true);
    setCheckLoading(true);
    setCheckError(null);
    setCheckData(null);
    try {
      const response = await fetch(`/api/check-run?run=${encodeURIComponent(run)}`);
      const data = await response.json();
      if (response.ok) {
        setCheckData(data);
      } else {
        setCheckError(data.error || 'Failed to check run');
      }
    } catch (err) {
      console.error('Check run failed:', err);
      setCheckError('Failed to check run');
    } finally {
      setCheckLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", overflow: "hidden" }}>
      <header style={{
        display: "flex",
        alignItems: "center",
        gap: isMobile ? 8 : 12,
        padding: isMobile ? "0 12px" : "0 24px",
        height: 64,
        borderBottom: "1px solid #112a45",
        background: "#001529",
        flexShrink: 0,
        lineHeight: "normal"
      }}>
        <Button
          type="text"
          icon={siderCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={() => setSiderCollapsed((v) => !v)}
          aria-label={siderCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          style={{ color: "#fff", flexShrink: 0 }}
        />
        <Title level={isMobile ? 5 : 4} style={{ color: "#fff", margin: 0, fontWeight: 700, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {isMobile ? "W2C" : "Widget2Code"}
        </Title>
        {!isMobile && (
          <div style={{ display: "flex", gap: 8, marginLeft: 16 }}>
            <Link href="/" prefetch passHref legacyBehavior>
              <a style={{ textDecoration: 'none' }}>
                <Button type="primary" icon={<EyeOutlined />} style={{ background: "#1677ff", borderColor: "#1677ff" }}>
                  Viewer
                </Button>
              </a>
            </Link>
            <Link href="/playground" prefetch passHref legacyBehavior>
              <a style={{ textDecoration: 'none' }}>
                <Button icon={<ExperimentOutlined />} style={{ background: "#434343", borderColor: "#434343", color: "#fff" }}>
                  Playground
                </Button>
              </a>
            </Link>
          </div>
        )}
        <div style={{ flex: 1 }} />
        <div style={{ width: isMobile ? 'min(85vw, 480px)' : 'clamp(480px, 50vw, 1000px)' }}>
          <RunPicker
            runs={runs}
            value={run}
            onChange={(v) => {
              setLoadingImages(true);
              setImages([]);
              setSelected(null);
              setRun(v);
              router.push(`/?run=${encodeURIComponent(v)}`, undefined, { shallow: true });
            }}
          />
        </div>
      </header>

      <div style={{ display: "flex", flex: 1, overflow: "hidden", position: "relative" }}>
        {/* Mobile overlay to close sidebar */}
        {isMobile && !siderCollapsed && (
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: "rgba(0, 0, 0, 0.5)",
              zIndex: 999,
              cursor: "pointer"
            }}
            onClick={() => setSiderCollapsed(true)}
          />
        )}

        <Sider
          width={isMobile ? "100%" : 320}
          collapsedWidth={0}
          collapsible
          collapsed={siderCollapsed}
          trigger={null}
          className="appSider"
          style={{
            background: "#fff",
            borderRight: "1px solid #e8e8e8",
            boxShadow: "2px 0 8px rgba(0,0,0,0.05)",
            position: isMobile ? "absolute" : "relative",
            zIndex: isMobile ? 1000 : "auto",
            height: "100%",
            maxWidth: isMobile ? "85vw" : "none"
          }}
        >
          <div style={{
            padding: "16px 16px 12px",
            flexShrink: 0
          }}>
            <Input
              placeholder="Search images..."
              allowClear
              onChange={(e) => setFilter(e.target.value)}
              value={filter}
              size="large"
              style={{ borderRadius: 8 }}
            />
          </div>

          <div style={{
            flex: 1,
            overflow: "auto",
            padding: "0 12px 12px"
          }}>
            {loadingImages ? (
              <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: 200 }}>
                <Spin />
              </div>
            ) : filtered.length ? (
              filtered.map((item) => (
                <div
                  key={item.id}
                  onClick={() => setSelected(item.id)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    padding: 12,
                    marginBottom: 8,
                    cursor: "pointer",
                    background: selected === item.id ? "#f0f7ff" : "#fafafa",
                    border: selected === item.id ? "2px solid #1677ff" : "2px solid transparent",
                    borderRadius: 12,
                    transition: "all 0.2s",
                    boxShadow: selected === item.id ? "0 2px 8px rgba(22,119,255,0.15)" : "none"
                  }}
                  onMouseEnter={(e) => {
                    if (selected !== item.id) {
                      e.currentTarget.style.background = "#f5f5f5";
                      e.currentTarget.style.transform = "translateX(2px)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (selected !== item.id) {
                      e.currentTarget.style.background = "#fafafa";
                      e.currentTarget.style.transform = "translateX(0)";
                    }
                  }}
                >
                  <div style={{
                    width: 56,
                    height: 56,
                    flexShrink: 0,
                    borderRadius: 8,
                    overflow: "hidden",
                    background: "#fff",
                    border: "1px solid #e8e8e8",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center"
                  }}>
                    {item.source ? (
                      <img
                        loading="lazy"
                        src={`/api/thumbnail?run=${encodeURIComponent(run)}&file=${encodeURIComponent(item.source)}`}
                        alt={item.id}
                        style={{ width: "100%", height: "100%", objectFit: "cover" }}
                      />
                    ) : (
                      <Text type="secondary" style={{ fontSize: 18, fontWeight: 500 }}>?</Text>
                    )}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      fontWeight: 500,
                      fontSize: 14,
                      color: selected === item.id ? "#1677ff" : "#262626",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      marginBottom: 4
                    }}>
                      {item.id}
                    </div>
                    {item.source && (
                      <Text type="secondary" style={{
                        fontSize: 12,
                        display: "block",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap"
                      }}>
                        {item.source.split("/").pop()}
                      </Text>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <Empty description="No images" style={{ marginTop: 48 }} />
            )}
          </div>
        </Sider>

        <main style={{
          flex: 1,
          overflow: "auto",
          padding: 16,
          background: "#fff"
        }}>
          {!selected ? (
            <Empty description="Select an image" />
          ) : loadingResults ? (
            <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: 240 }}>
              <Spin />
            </div>
          ) : (
            <div>
              <Flex align="center" gap={12} wrap={isMobile ? "wrap" : "nowrap"} style={{ marginBottom: 16 }}>
                <Title level={5} style={{ margin: 0, flexShrink: 0 }}>{selected}</Title>
                {selectedSource ? (
                  <img
                    alt="source"
                    src={selectedSource}
                    style={{ height: isMobile ? 48 : 64, borderRadius: 8, border: "1px solid #eef0f3", background: "#fff", cursor: "pointer", flexShrink: 0 }}
                    onClick={() => setSourceModalOpen(true)}
                  />
                ) : null}

                <div style={{
                  background: '#f5f5f5',
                  padding: isMobile ? '12px' : '16px 20px',
                  borderRadius: 12,
                  border: '1px solid #e8e8e8',
                  display: 'flex',
                  alignItems: 'center',
                  marginLeft: isMobile ? 0 : 'auto',
                  minHeight: isMobile ? 'auto' : 88,
                  width: isMobile ? '100%' : 'auto'
                }}>
                  <Flex gap={isMobile ? 8 : 12} align="center" wrap={isMobile ? "wrap" : "nowrap"} style={{ width: isMobile ? '100%' : 'auto' }}>
                    <Button
                      icon={<DownloadOutlined />}
                      onClick={handleDownloadAll}
                      disabled={!run}
                      size={isMobile ? "middle" : "large"}
                      style={{ flex: isMobile ? 1 : 'none' }}
                    >
                      {isMobile ? "Download" : "Download All"}
                    </Button>

                    <Button
                      icon={<CheckCircleOutlined />}
                      onClick={handleCheckRun}
                      disabled={!run}
                      size={isMobile ? "middle" : "large"}
                      style={{ flex: isMobile ? 1 : 'none' }}
                    >
                      {isMobile ? "Check" : "Check Run"}
                    </Button>
                  </Flex>
                </div>
              </Flex>

              <Divider style={{ margin: "8px 0 12px" }} />
              {Object.keys(results).length === 0 ? (
                <Empty description="No results" />
              ) : (
                Object.keys(results).sort().map((cat) => (
                  <div key={cat} style={{ marginBottom: 16 }}>
                    <div className="gridHeader">{cat}</div>
                    <div className="grid">
                      {results[cat].map((it) => (
                        <PreviewCard
                          key={it.name}
                          title={it.name}
                          codeUrl={it.codeUrl}
                          prompt={it.prompt}
                          sourceUrl={selectedSource}
                          run={run}
                          filePath={it.path}
                          renderStatus={renderStatus}
                          showCompare={true}
                        />
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </main>
      </div>

      <Modal
        open={sourceModalOpen}
        onCancel={() => setSourceModalOpen(false)}
        footer={null}
        width={900}
        centered
      >
        {selectedSource ? (
          <img
            alt="source"
            src={selectedSource}
            style={{ width: "100%", maxHeight: "70vh", objectFit: "contain", borderRadius: 8 }}
          />
        ) : null}
      </Modal>

      <CheckRunModal
        open={checkModalOpen}
        onClose={() => setCheckModalOpen(false)}
        run={run}
        data={checkData}
        loading={checkLoading}
        error={checkError}
      />
    </div>
  );
}
