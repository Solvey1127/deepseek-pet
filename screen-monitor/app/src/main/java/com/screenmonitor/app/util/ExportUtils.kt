package com.screenmonitor.app.util

import android.content.Context
import android.content.Intent
import com.screenmonitor.app.data.AppSession
import com.screenmonitor.app.data.ScreenSession
import com.screenmonitor.app.data.UsageDao

object ExportUtils {

    /** 生成指定日期的文本报告并通过系统分享发送（可转发到微信/QQ） */
    suspend fun shareDayReport(context: Context, dao: UsageDao, date: String) {
        val text = buildDayReport(dao, date)
        val sendIntent = Intent(Intent.ACTION_SEND).apply {
            type = "text/plain"
            putExtra(Intent.EXTRA_TEXT, text)
            putExtra(Intent.EXTRA_SUBJECT, "屏幕监测报告 $date")
        }
        context.startActivity(
            Intent.createChooser(sendIntent, "分享使用报告").apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
        )
    }

    /** 生成完整的多日报告文本 */
    suspend fun buildDayReport(dao: UsageDao, date: String): String {
        val sb = StringBuilder()
        sb.append("📱 屏幕监测报告  $date\n")
        sb.append("=".repeat(30)).append("\n\n")

        val totalScreen = dao.totalScreenMs(date) ?: 0L
        sb.append("【亮屏总时长】").append(TimeUtils.formatDurationDetail(totalScreen)).append("\n")

        val appRows = dao.appUsageByDate(date)
        if (appRows.isEmpty()) {
            sb.append("\n当天没有检测到应用使用记录。\n")
            return sb.toString()
        }

        sb.append("\n【应用使用排行】\n")
        appRows.forEachIndexed { i, row ->
            sb.append("${i + 1}. ${row.appName}  ${TimeUtils.formatDurationDetail(row.totalMs)}（${row.count}次）\n")
        }

        val sessions = dao.appSessionsByDate(date)
        sb.append("\n【使用时间线】\n")
        sessions.forEach { s ->
            sb.append(
                "${TimeUtils.formatClock(s.startTs)} - ${TimeUtils.formatClock(s.endTs)}  ${s.appName}  ${TimeUtils.formatDurationDetail(s.durationMs)}\n"
            )
        }
        return sb.toString()
    }

    /** 生成应用详情的 CSV 文本（可用表格软件打开） */
    suspend fun buildCsv(dao: UsageDao, date: String): String {
        val sb = StringBuilder()
        sb.append("日期,应用,开始时间,结束时间,时长秒\n")
        dao.appSessionsByDate(date).forEach { s ->
            sb.append(
                "${s.date},${s.appName},${TimeUtils.formatClock(s.startTs)},${TimeUtils.formatClock(s.endTs)},${s.durationMs / 1000}\n"
            )
        }
        return sb.toString()
    }
}
