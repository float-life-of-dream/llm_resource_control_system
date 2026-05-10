from app.services.monitor_service import MonitorService


class FakePrometheusClient:
    def query(self, promql):
        responses = {
            "DCGM_FI_DEV_FB_USED": {
                "result": [
                    {"metric": {"UUID": "GPU-1", "gpu": "0", "modelName": "NVIDIA A100"}, "value": [1, "8192"]}
                ]
            },
            "DCGM_FI_DEV_FB_TOTAL": {
                "result": [
                    {"metric": {"UUID": "GPU-1", "gpu": "0", "modelName": "NVIDIA A100"}, "value": [1, "40960"]}
                ]
            },
            "DCGM_FI_DEV_GPU_UTIL": {
                "result": [
                    {"metric": {"UUID": "GPU-1", "gpu": "0", "modelName": "NVIDIA A100"}, "value": [1, "72"]}
                ]
            },
            "100 * DCGM_FI_DEV_FB_USED / clamp_min(DCGM_FI_DEV_FB_TOTAL, 1)": {
                "result": [
                    {"metric": {"UUID": "GPU-1", "gpu": "0", "modelName": "NVIDIA A100"}, "value": [1, "20"]}
                ]
            },
            "DCGM_FI_DEV_GPU_TEMP": {
                "result": [
                    {"metric": {"UUID": "GPU-1", "gpu": "0", "modelName": "NVIDIA A100"}, "value": [1, "64"]}
                ]
            },
            "DCGM_FI_DEV_POWER_USAGE": {
                "result": [
                    {"metric": {"UUID": "GPU-1", "gpu": "0", "modelName": "NVIDIA A100"}, "value": [1, "218"]}
                ]
            },
        }
        return responses[promql]


def test_get_gpu_devices_merges_dcgm_metrics_by_uuid():
    result = MonitorService(FakePrometheusClient()).get_gpu_devices()

    assert result["items"][0]["id"] == "GPU-1"
    assert result["items"][0]["name"] == "NVIDIA A100"
    assert result["items"][0]["memoryUsedMiB"] == 8192
    assert result["items"][0]["memoryTotalMiB"] == 40960
    assert result["items"][0]["utilizationPercent"] == 72
    assert result["items"][0]["status"] == "active"
