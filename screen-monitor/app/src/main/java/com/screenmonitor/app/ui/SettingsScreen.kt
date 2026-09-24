package com.screenmonitor.app.ui

import android.content.Context
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.screenmonitor.app.data.AppDatabase
import com.screenmonitor.app.data.Permissions
import com.screenmonitor.app.data.UsageCollector
import com.screenmonitor.app.util.ExportUtils
import com.screenmonitor.app.util.TimeUtils
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@Composable
fun SettingsScreen() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val dao = remember { AppDatabase.get(context).usageDao() }

    var hasAccess by remember { mutableStateOf(Permissions.hasUsageAccess(context)) }
    var lastCollect by remember { mutableStateOf(readLastCollect(context)) }
    var refreshing by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf("") }

    suspend fun refresh() {
        refreshing = true
        message = ""
        try {
            withContext(Dispatchers.IO) {
                UsageCollector.collect(context, dao)
                writeLastCollect(context, System.currentTimeMillis())
            }
            lastCollect = readLastCollect(context)
            hasAccess = Permissions.hasUsageAccess(context)
            message = if (hasAccess) "已刷新，数据已更新" else "尚未授权，无法采集"
        } catch (e: Exception) {
            message = "刷新失败：${e.message}"
        }
        refreshing = false
    }

    LaunchedEffect(Unit) {
        hasAccess = Permissions.hasUsageAccess(context)
        lastCollect = readLastCollect(context)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text("设置", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(4.dp))

        // 权限状态
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.fillMaxWidth().padding(16.dp)) {
                Text("使用情况访问权限", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(4.dp))
                Text(
                    if (hasAccess) "✅ 已授权，可正常采集" else "❌ 未授权，无法记录使用情况",
                    style = MaterialTheme.typography.bodyMedium,
                    color = if (hasAccess) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error
                )
                if (!hasAccess) {
                    Spacer(Modifier.height(8.dp))
                    Button(
                        onClick = { Permissions.openUsageAccessSettings(context) },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("去开启权限")
                    }
                }
            }
        }

        // 后台运行
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.fillMaxWidth().padding(16.dp)) {
                Text("后台运行（可选）", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(4.dp))
                Text(
                    "允许后台运行可让系统更及时保留本应用。\n（数据不依赖后台，打开应用即可补全最近记录）",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(Modifier.height(8.dp))
                OutlinedButton(
                    onClick = { Permissions.openBatteryOptimizationSettings(context) },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("允许后台运行")
                }
            }
        }

        // 数据操作
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.fillMaxWidth().padding(16.dp)) {
                Text("数据操作", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(8.dp))
                Button(
                    onClick = {
                        scope.launch {
                            refreshing = true
                            message = ""
                            try {
                                withContext(Dispatchers.IO) {
                                    UsageCollector.collect(context, dao)
                                    writeLastCollect(context, System.currentTimeMillis())
                                }
                                hasAccess = Permissions.hasUsageAccess(context)
                                message = if (hasAccess) "已刷新" else "尚未授权，无法采集"
                            } catch (e: Exception) {
                                message = "刷新失败：${e.message}"
                            }
                            refreshing = false
                        }
                    },
                    enabled = !refreshing,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(if (refreshing) "刷新中…" else "立即刷新数据")
                }
                Spacer(Modifier.height(8.dp))
                OutlinedButton(
                    onClick = {
                        scope.launch {
                            try {
                                withContext(Dispatchers.IO) {
                                    UsageCollector.collect(context, dao)
                                }
                                ExportUtils.shareDayReport(context, dao, TimeUtils.today())
                            } catch (e: Exception) {
                                message = "导出失败：${e.message}"
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("导出今日报告（可发微信）")
                }
                Spacer(Modifier.height(8.dp))
                OutlinedButton(
                    onClick = {
                        scope.launch {
                            try {
                                val today = TimeUtils.today()
                                val csv = withContext(Dispatchers.IO) { ExportUtils.buildCsv(dao, today) }
                                val sendIntent = android.content.Intent(android.content.Intent.ACTION_SEND).apply {
                                    type = "text/csv"
                                    putExtra(android.content.Intent.EXTRA_TEXT, csv)
                                    putExtra(android.content.Intent.EXTRA_SUBJECT, "使用记录CSV $today")
                                }
                                context.startActivity(
                                    android.content.Intent.createChooser(sendIntent, "导出CSV").apply {
                                        addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
                                    }
                                )
                            } catch (e: Exception) {
                                message = "导出失败：${e.message}"
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("导出今日CSV明细")
                }
            }
        }

        if (message.isNotEmpty()) {
            Text(message, color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.bodyMedium)
        }

        // 状态信息
        Row(Modifier.fillMaxWidth()) {
            Text(
                "最后采集：" + (if (lastCollect > 0) TimeUtils.formatClock(lastCollect) else "从未"),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(Modifier.weight(1f))
            Text(
                "数据仅保存在本机",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        Text(
            "本应用通过 Android 系统官方「使用情况访问」机制记录数据，\n不读取任何屏幕内容，不上传网络。",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

private const val PREFS = "screen_monitor_prefs"
private const val KEY_LAST_COLLECT = "last_collect_ts"

private fun readLastCollect(context: Context): Long {
    val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
    return prefs.getLong(KEY_LAST_COLLECT, 0L)
}

private fun writeLastCollect(context: Context, ts: Long) {
    context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        .edit()
        .putLong(KEY_LAST_COLLECT, ts)
        .apply()
}
